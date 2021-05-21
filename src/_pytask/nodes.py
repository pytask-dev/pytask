"""Deals with nodes which are dependencies or products of a task."""
import functools
import inspect
import itertools
import pathlib
from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple
from typing import Union

import attr
from _pytask.console import escape_squared_brackets
from _pytask.exceptions import NodeNotCollectedError
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark import get_marks_from_obj
from _pytask.path import find_closest_ancestor
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to
from _pytask.shared import find_duplicates


def depends_on(objects: Union[Any, Iterable[Any]]) -> Union[Any, Iterable[Any]]:
    """Specify dependencies for a task.

    Parameters
    ----------
    objects : Union[Any, Iterable[Any]]
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`pytask.hookspecs.pytask_collect_node` entry-point.

    """
    return objects


def produces(objects: Union[Any, Iterable[Any]]) -> Union[Any, Iterable[Any]]:
    """Specify products of a task.

    Parameters
    ----------
    objects : Union[Any, Iterable[Any]]
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation for the
        :func:`pytask.hookspecs.pytask_collect_node` entry-point.

    """
    return objects


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes."""

    @abstractmethod
    def state(self):
        """Return a value which indicates whether a node has changed or not."""
        pass


class MetaTask(MetaNode):
    """The base class for tasks."""

    @abstractmethod
    def execute(self):
        """Execute the task."""
        pass


@attr.s
class PythonFunctionTask(MetaTask):
    """The class for tasks which are Python functions."""

    base_name = attr.ib(type=str)
    """str: The base name of the task."""
    name = attr.ib(type=str)
    """str: The unique identifier for a task."""
    path = attr.ib(type=Path)
    """pathlib.Path: Path to the file where the task was defined."""
    function = attr.ib(type=callable)
    """callable: The task function."""
    depends_on = attr.ib(factory=dict)
    """Optional[List[MetaNode]]: A list of dependencies of task."""
    produces = attr.ib(factory=dict)
    """List[MetaNode]: A list of products of task."""
    markers = attr.ib(factory=list)
    """Optional[List[Mark]]: A list of markers attached to the task function."""
    keep_dict = attr.ib(default=False)
    """Dict[str, bool]: Should dictionaries for single nodes be preserved?"""
    _report_sections = attr.ib(factory=list)
    """List[Tuple[str]]: A list of reports with entries for when, what, and content."""
    attributes = attr.ib(factory=dict)
    """Dict[Any, Any]: A dictionary to store additional information of the task."""

    @classmethod
    def from_path_name_function_session(cls, path, name, function, session):
        """Create a task from a path, name, function, and session."""
        keep_dictionary = {}

        objects = _extract_nodes_from_function_markers(function, depends_on)
        nodes, keep_dict = _convert_objects_to_node_dictionary(objects, "depends_on")
        keep_dictionary["depends_on"] = keep_dict
        dependencies = _collect_nodes(session, path, name, nodes)

        objects = _extract_nodes_from_function_markers(function, produces)
        nodes, keep_dict = _convert_objects_to_node_dictionary(objects, "produces")
        keep_dictionary["produces"] = keep_dict
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

    def execute(self):
        """Execute the task."""
        kwargs = self._get_kwargs_from_task_for_function()
        self.function(**kwargs)

    def state(self):
        """Return the last modified date of the file where the task is defined."""
        return str(self.path.stat().st_mtime)

    def _get_kwargs_from_task_for_function(self):
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

    def add_report_section(self, when: str, key: str, content: str):
        if content:
            self._report_sections.append((when, key, content))


@attr.s
class FilePathNode(MetaNode):
    """The class for a node which is a path."""

    name = attr.ib()
    """str: Name of the node which makes it identifiable in the DAG."""

    value = attr.ib()
    """Any: Value passed to the decorator which can be requested inside the function."""

    path = attr.ib()
    """pathlib.Path: Path to the FilePathNode."""

    @classmethod
    @functools.lru_cache()
    def from_path(cls, path: pathlib.Path):
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            raise ValueError("FilePathNode must be instantiated from absolute path.")
        return cls(path.as_posix(), path, path)

    def state(self):
        """Return the last modified date for file path."""
        if not self.path.exists():
            raise NodeNotFoundError
        else:
            return str(self.path.stat().st_mtime)


def _collect_nodes(
    session, path: Path, name: str, nodes: Dict[str, Union[str, Path]]
) -> Dict[str, Path]:
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
    Dict[str, Path]
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
                f"'{node}' cannot be parsed as a dependency or product for task "
                f"'{name}' in '{path}'."
            )
        else:
            collected_nodes[node_name] = collected_node

    return collected_nodes


def _extract_nodes_from_function_markers(function, parser):
    """Extract nodes from a marker.

    The parser is a functions which is used to document the marker with the correct
    signature. Using the function as a parser for the ``args`` and ``kwargs`` of the
    marker provides the expected error message for misspecification.

    """
    marker_name = parser.__name__
    for marker in get_marks_from_obj(function, marker_name):
        parsed = parser(*marker.args, **marker.kwargs)
        yield parsed


def _convert_objects_to_node_dictionary(objects, when):
    """Convert objects to node dictionary."""
    list_of_tuples, keep_dict = _convert_objects_to_list_of_tuples(objects, when)
    _check_that_names_are_not_used_multiple_times(list_of_tuples, when)
    nodes = _convert_nodes_to_dictionary(list_of_tuples)
    return nodes, keep_dict


def _convert_objects_to_list_of_tuples(objects, when: str):
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


def _check_that_names_are_not_used_multiple_times(list_of_tuples, when):
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
    list_of_tuples: List[Tuple[str]],
) -> Dict[str, Union[str, Path]]:
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


def create_task_name(path: Path, base_name: str):
    """Create the name of a task from a path and the task's base name.

    Examples
    --------
    >>> from pathlib import Path
    >>> create_task_name(Path("module.py"), "task_dummy")
    'module.py::task_dummy'

    """
    return path.as_posix() + "::" + base_name


def reduce_node_name(node, paths: List[Path]):
    """Reduce the node name.

    The whole name of the node - which includes the drive letter - can be very long
    when using nested folder structures in bigger projects.

    Thus, the part of the name which contains the path is replaced by the relative
    path from one path in ``session.config["paths"]`` to the node.

    """
    ancestor = find_closest_ancestor(node.path, paths)
    if ancestor is None:
        try:
            ancestor = find_common_ancestor(node.path, *paths)
        except ValueError:
            ancestor = node.path.parents[-1]

    if isinstance(node, MetaTask):
        shortened_path = relative_to(node.path, ancestor)
        raw_name = create_task_name(shortened_path, node.base_name)
        name = escape_squared_brackets(raw_name)
    elif isinstance(node, MetaNode):
        name = relative_to(node.path, ancestor).as_posix()
    else:
        raise ValueError(f"Unknown node {node} with type '{type(node)}'.")

    return name


def reduce_names_of_multiple_nodes(names, dag, paths):
    """Reduce the names of multiple nodes in the DAG."""
    return [
        reduce_node_name(dag.nodes[n].get("node") or dag.nodes[n].get("task"), paths)
        for n in names
    ]
