"""Deals with nodes which are dependencies or products of a task."""
import functools
import inspect
import itertools
from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

import attr
from _pytask.exceptions import NodeNotCollectedError
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark_utils import get_marks_from_obj
from _pytask.session import Session


if TYPE_CHECKING:
    from _pytask.mark import Mark


def depends_on(
    objects: Union[Any, Iterable[Any], Dict[Any, Any]]
) -> Union[Any, Iterable[Any], Dict[Any, Any]]:
    """Specify dependencies for a task.

    Parameters
    ----------
    objects : Union[Any, Iterable[Any], Dict[Any, Any]]
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`pytask.hookspecs.pytask_collect_node` entry-point.

    """
    return objects


def produces(
    objects: Union[Any, Iterable[Any], Dict[Any, Any]]
) -> Union[Any, Iterable[Any], Dict[Any, Any]]:
    """Specify products of a task.

    Parameters
    ----------
    objects : Union[Any, Iterable[Any], Dict[Any, Any]]
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`pytask.hookspecs.pytask_collect_node` entry-point.

    """
    return objects


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes."""

    name: str
    path: Path

    @abstractmethod
    def state(self) -> Optional[str]:
        ...


class MetaTask(MetaNode):
    """The base class for tasks."""

    base_name: str
    name: str
    short_name: Optional[str]
    markers: List["Mark"]
    depends_on: Dict[str, MetaNode]
    produces: Dict[str, MetaNode]
    path: Path
    function: Optional[Callable[..., Any]]
    attributes: Dict[Any, Any]
    _report_sections: List[Tuple[str, str, str]]

    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def add_report_section(
        self, when: str, key: str, content: str  # noqa: U100
    ) -> None:
        ...


@attr.s
class PythonFunctionTask(MetaTask):
    """The class for tasks which are Python functions."""

    base_name = attr.ib(type=str)
    """str: The base name of the task."""
    name = attr.ib(type=str)
    """str: The unique identifier for a task."""
    path = attr.ib(type=Path)
    """pathlib.Path: Path to the file where the task was defined."""
    function = attr.ib(type=Callable[..., Any])
    """Callable[..., Any]: The task function."""
    short_name = attr.ib(default=None, type=Optional[str], init=False)
    """str: The shortest uniquely identifiable name for task for display."""
    depends_on = attr.ib(factory=dict, type=Dict[str, MetaNode])
    """Dict[str, MetaNode]: A list of dependencies of task."""
    produces = attr.ib(factory=dict, type=Dict[str, MetaNode])
    """Dict[str, MetaNode]: A list of products of task."""
    markers = attr.ib(factory=list, type="List[Mark]")
    """Optional[List[Mark]]: A list of markers attached to the task function."""
    keep_dict = attr.ib(factory=dict, type=Dict[str, bool])
    """Dict[str, bool]: Should dictionaries for single nodes be preserved?"""
    _report_sections = attr.ib(factory=list, type=List[Tuple[str, str, str]])
    """List[Tuple[str, str, str]]: Reports with entries for when, what, and content."""
    attributes = attr.ib(factory=dict, type=Dict[Any, Any])
    """Dict[Any, Any]: A dictionary to store additional information of the task."""

    def __attrs_post_init__(self: "PythonFunctionTask") -> None:
        if self.short_name is None:
            self.short_name = self.name

    @classmethod
    def from_path_name_function_session(
        cls, path: Path, name: str, function: Callable[..., Any], session: Session
    ) -> "PythonFunctionTask":
        """Create a task from a path, name, function, and session."""
        keep_dictionary = {}

        objects = _extract_nodes_from_function_markers(function, depends_on)
        nodes, keep_dict_de = _convert_objects_to_node_dictionary(objects, "depends_on")
        keep_dictionary["depends_on"] = keep_dict_de
        dependencies = _collect_nodes(session, path, name, nodes)

        objects = _extract_nodes_from_function_markers(function, produces)
        nodes, keep_dict_prod = _convert_objects_to_node_dictionary(objects, "produces")
        keep_dictionary["produces"] = keep_dict_prod
        products = _collect_nodes(session, path, name, nodes)

        markers = [
            marker
            for marker in getattr(function, "pytaskmark", [])
            if marker.name not in ["depends_on", "produces"]
        ]

        return cls(
            base_name=name,
            name=create_task_name(path, name),
            path=path,
            function=function,
            depends_on=dependencies,
            produces=products,
            markers=markers,
            keep_dict=keep_dictionary,
        )

    def execute(self) -> None:
        """Execute the task."""
        kwargs = self._get_kwargs_from_task_for_function()
        self.function(**kwargs)

    def state(self) -> str:
        """Return the last modified date of the file where the task is defined."""
        return str(self.path.stat().st_mtime)

    def _get_kwargs_from_task_for_function(self) -> Dict[str, Any]:
        """Process dependencies and products to pass them as kwargs to the function."""
        func_arg_names = set(inspect.signature(self.function).parameters)
        kwargs = {}
        for arg_name in ["depends_on", "produces"]:
            if arg_name in func_arg_names:
                attribute = getattr(self, arg_name)
                kwargs[arg_name] = (
                    attribute[0].value
                    if len(attribute) == 1
                    and 0 in attribute
                    and not self.keep_dict[arg_name]
                    else {name: node.value for name, node in attribute.items()}
                )

        return kwargs

    def add_report_section(self, when: str, key: str, content: str) -> None:
        if content:
            self._report_sections.append((when, key, content))


@attr.s
class FilePathNode(MetaNode):
    """The class for a node which is a path."""

    name = attr.ib(type=str)
    """str: Name of the node which makes it identifiable in the DAG."""

    value = attr.ib(type=Path)
    """Any: Value passed to the decorator which can be requested inside the function."""

    path = attr.ib(type=Path)
    """pathlib.Path: Path to the FilePathNode."""

    @classmethod
    @functools.lru_cache()
    def from_path(cls, path: Path) -> "FilePathNode":
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            raise ValueError("FilePathNode must be instantiated from absolute path.")
        return cls(path.as_posix(), path, path)

    def state(self) -> Optional[str]:
        """Return the last modified date for file path."""
        if not self.path.exists():
            raise NodeNotFoundError
        else:
            return str(self.path.stat().st_mtime)


def _collect_nodes(
    session: Session, path: Path, name: str, nodes: Dict[str, Union[str, Path]]
) -> Dict[str, MetaNode]:
    """Collect nodes for a task.

    Parameters
    ----------
    session : _pytask.session.Session
        The session.
    path : Path
        The path to the task whose nodes are collected.
    name : str
        The name of the task.
    nodes : Dict[str, Union[str, Path]]
        A dictionary of nodes parsed from the ``depends_on`` or ``produces`` markers.

    Returns
    -------
    Dict[str, MetaNode]
        A dictionary of node names and their paths.

    Raises
    ------
    NodeNotCollectedError
        If the node could not collected.

    """
    collected_nodes = {}

    for node_name, node in nodes.items():
        collected_node = session.hook.pytask_collect_node(
            session=session, path=path, node=node
        )
        if collected_node is None:
            raise NodeNotCollectedError(
                f"{node!r} cannot be parsed as a dependency or product for task "
                f"{name!r} in {path!r}."
            )
        else:
            collected_nodes[node_name] = collected_node

    return collected_nodes


def _extract_nodes_from_function_markers(
    function: Callable[..., Any], parser: Callable[..., Any]
) -> Generator[Any, None, None]:
    """Extract nodes from a marker.

    The parser is a functions which is used to document the marker with the correct
    signature. Using the function as a parser for the ``args`` and ``kwargs`` of the
    marker provides the expected error message for misspecification.

    """
    marker_name = parser.__name__
    for marker in get_marks_from_obj(function, marker_name):
        parsed = parser(*marker.args, **marker.kwargs)
        yield parsed


def _convert_objects_to_node_dictionary(
    objects: Any, when: str
) -> Tuple[Dict[Any, Any], bool]:
    """Convert objects to node dictionary."""
    list_of_tuples, keep_dict = _convert_objects_to_list_of_tuples(objects, when)
    _check_that_names_are_not_used_multiple_times(list_of_tuples, when)
    nodes = _convert_nodes_to_dictionary(list_of_tuples)
    return nodes, keep_dict


def _convert_objects_to_list_of_tuples(
    objects: Union[Any, Tuple[Any, Any], List[Any], List[Tuple[Any, Any]]], when: str
) -> Tuple[List[Tuple[Any, ...]], bool]:
    """Convert objects to list of tuples.

    Examples
    --------
    _convert_objects_to_list_of_tuples([{0: 0}, [4, (3, 2)], ((1, 4),))
    [(0, 0), (4,), (3, 2), (1, 4)], False

    """
    keep_dict = False

    out = []
    for obj in objects:
        if isinstance(obj, dict):
            obj = obj.items()

        if isinstance(obj, Iterable) and not isinstance(obj, str):
            keep_dict = True
            for x in obj:
                if isinstance(x, Iterable) and not isinstance(x, str):
                    tuple_x = tuple(x)
                    if len(tuple_x) in [1, 2]:
                        out.append(tuple_x)
                    else:
                        name = "Dependencies" if when == "depends_on" else "Products"
                        raise ValueError(
                            f"{name} in pytask.mark.{when} can be given as a value or "
                            "a name and a value which is 1 or 2 elements. The "
                            f"following node has {len(tuple_x)} elements: {tuple_x}."
                        )
                else:
                    out.append((x,))
        else:
            out.append((obj,))

    if len(out) > 1:
        keep_dict = False

    return out, keep_dict


def _check_that_names_are_not_used_multiple_times(
    list_of_tuples: List[Tuple[Any, ...]], when: str
) -> None:
    """Check that names of nodes are not assigned multiple times.

    Tuples in the list have either one or two elements. The first element in the two
    element tuples is the name and cannot occur twice.

    Examples
    --------
    >>> _check_that_names_are_not_used_multiple_times(
    ...     [("a",), ("a", 1)], "depends_on"
    ... )
    >>> _check_that_names_are_not_used_multiple_times(
    ...     [("a", 0), ("a", 1)], "produces"
    ... )
    Traceback (most recent call last):
    ValueError: '@pytask.mark.produces' has nodes with the same name: {'a'}

    """
    names = [x[0] for x in list_of_tuples if len(x) == 2]
    duplicated = find_duplicates(names)

    if duplicated:
        raise ValueError(
            f"'@pytask.mark.{when}' has nodes with the same name: {duplicated}"
        )


def _convert_nodes_to_dictionary(
    list_of_tuples: List[Tuple[Any, ...]]
) -> Dict[Any, Any]:
    """Convert nodes to dictionaries.

    Examples
    --------
    >>> _convert_nodes_to_dictionary([(0,), (1,)])
    {0: 0, 1: 1}
    >>> _convert_nodes_to_dictionary([(1, 0), (1,)])
    {1: 0, 0: 1}

    """
    nodes = {}
    counter = itertools.count()
    names = [x[0] for x in list_of_tuples if len(x) == 2]

    for tuple_ in list_of_tuples:
        if len(tuple_) == 2:
            node_name, node = tuple_
            nodes[node_name] = node

        else:
            while True:
                node_name = next(counter)
                if node_name not in names:
                    break

            nodes[node_name] = tuple_[0]

    return nodes


def create_task_name(path: Path, base_name: str) -> str:
    """Create the name of a task from a path and the task's base name.

    Examples
    --------
    >>> from pathlib import Path
    >>> create_task_name(Path("module.py"), "task_dummy")
    'module.py::task_dummy'

    """
    return path.as_posix() + "::" + base_name


def find_duplicates(x: Iterable[Any]) -> Set[Any]:
    """Find duplicated entries in iterable.

    Examples
    --------
    >>> find_duplicates(["a", "b", "a"])
    {'a'}
    >>> find_duplicates(["a", "b"])
    set()

    """
    seen = set()
    duplicates = set()

    for i in x:
        if i in seen:
            duplicates.add(i)
        seen.add(i)

    return duplicates
