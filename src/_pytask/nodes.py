"""Deals with nodes which are dependencies or products of a task."""
import functools
import inspect
import pathlib
from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Union

import attr
from _pytask.exceptions import NodeNotCollectedError
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark import get_marks_from_obj
from _pytask.shared import to_list


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


class MetaTask(metaclass=ABCMeta):
    """The base class for tasks."""

    @abstractmethod
    def execute(self):
        """Execute the task."""
        pass

    @abstractmethod
    def state(self):
        """Return a value to check whether the task definition has changed."""
        pass


@attr.s
class PythonFunctionTask(MetaTask):
    """The class for tasks which are Python functions."""

    name = attr.ib(type=str)
    """str: The unique identifier for a task."""
    path = attr.ib(type=Path)
    """pathlib.Path: Path to the file where the task was defined."""
    function = attr.ib(type=callable)
    """callable: The task function."""
    depends_on = attr.ib(converter=to_list)
    """Optional[List[MetaNode]]: A list of dependencies of task."""
    produces = attr.ib(converter=to_list)
    """List[MetaNode]: A list of products of task."""
    markers = attr.ib()
    """Optional[List[Mark]]: A list of markers attached to the task function."""

    @classmethod
    def from_path_name_function_session(cls, path, name, function, session):
        """Create a task from a path, name, function, and session."""
        objects = _extract_nodes_from_function_markers(function, depends_on)
        dependencies = _collect_nodes(session, path, name, objects)

        objects = _extract_nodes_from_function_markers(function, produces)
        products = _collect_nodes(session, path, name, objects)

        markers = [
            marker
            for marker in getattr(function, "pytaskmark", [])
            if marker.name not in ["depends_on", "produces"]
        ]

        return cls(
            path=path,
            name=path.as_posix() + "::" + name,
            function=function,
            depends_on=dependencies,
            produces=products,
            markers=markers,
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
        for name in ["depends_on", "produces"]:
            if name in func_arg_names:
                attribute = getattr(self, name)
                kwargs[name] = (
                    attribute[0].value
                    if len(attribute) == 1
                    else [node.value for node in attribute]
                )

        return kwargs


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes."""

    @abstractmethod
    def state(self):
        """Return a value which indicates whether a node has changed or not."""
        pass


@attr.s
class FilePathNode(MetaNode):
    """The class for a node which is a path."""

    name = attr.ib()
    """str: Name of the node which makes it identifiable in the DAG."""

    value = attr.ib()
    """Any: Value passed to the decorator which can be requested inside the function."""

    @classmethod
    @functools.lru_cache()
    def from_path(cls, path: pathlib.Path):
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        path = path.resolve()
        return cls(path.as_posix(), path)

    def state(self):
        """Return the last modified date for file path."""
        if not self.value.exists():
            raise NodeNotFoundError
        else:
            return str(self.value.stat().st_mtime)


def _collect_nodes(session, path, name, nodes):
    """Collect nodes for a task."""
    collect_nodes = []
    for node in nodes:
        collected_node = session.hook.pytask_collect_node(path=path, node=node)
        if collected_node is None:
            raise NodeNotCollectedError(
                f"'{node}' cannot be parsed as a dependency or product for task "
                f"'{name}' in '{path}'."
            )
        else:
            collect_nodes.append(collected_node)

    return collect_nodes


def _extract_nodes_from_function_markers(function, parser):
    """Extract nodes from a marker.

    The parser is a functions which is used to document the marker with the correct
    signature. Using the function as a parser for the ``args`` and ``kwargs`` of the
    marker provides the expected error message for misspecification.

    """
    marker_name = parser.__name__
    for marker in get_marks_from_obj(function, marker_name):
        yield from to_list(parser(*marker.args, **marker.kwargs))
