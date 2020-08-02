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
from pytask.exceptions import NodeNotCollectedError
from pytask.exceptions import NodeNotFoundError
from pytask.mark.structures import get_marks_from_obj
from pytask.shared import to_list


def depends_on(objects: Union[Any, Iterable[Any]]) -> Union[Any, Iterable[Any]]:
    """Specify a dependency of a task.

    Parameters
    ----------
    objects : Union[Any, Iterable[Any]]
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation.

    """
    return objects


def produces(objects: Union[Any, Iterable[Any]]) -> Union[Any, Iterable[Any]]:
    """Specify a product of a task.

    Parameters
    ----------
    objects : Union[Any, Iterable[Any]]
        Can be any valid Python object or an iterable of any Python objects. To be
        valid, it must be parsed by some hook implementation.

    """
    return objects


class MetaTask(metaclass=ABCMeta):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def state(self):
        pass


@attr.s
class PythonFunctionTask(MetaTask):

    name = attr.ib(type=str)
    path = attr.ib(type=Path)
    function = attr.ib()
    depends_on = attr.ib(converter=to_list)
    produces = attr.ib(converter=to_list)
    markers = attr.ib()

    @classmethod
    def from_path_name_function_session(cls, path, name, function, session):
        objects = extract_nodes_from_function_markers(function, depends_on)
        dependencies = collect_nodes(session, path, name, objects)

        objects = extract_nodes_from_function_markers(function, produces)
        products = collect_nodes(session, path, name, objects)

        markers = [
            marker
            for marker in getattr(function, "pytaskmark", [])
            if marker.name not in ["depends_on", "produces"]
        ]

        return cls(
            path=path,
            name=name,
            function=function,
            depends_on=dependencies,
            produces=products,
            markers=markers,
        )

    def execute(self):
        kwargs = self._get_kwargs_from_task_for_function()
        self.function(**kwargs)

    def state(self):
        return str(self.path.stat().st_mtime)

    def _get_kwargs_from_task_for_function(self):
        func_arg_names = set(inspect.signature(self.function).parameters)
        kwargs = {}
        if "depends_on" in func_arg_names:
            kwargs["depends_on"] = (
                self.depends_on[0].value
                if len(self.depends_on) == 1
                else [node.value for node in self.depends_on]
            )
        if "produces" in func_arg_names:
            kwargs["produces"] = (
                self.produces[0].value
                if len(self.produces) == 1
                else [node.value for node in self.produces]
            )

        return kwargs


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes."""

    @abstractmethod
    def state(self):
        pass


@attr.s
class FilePathNode(MetaNode):
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
        return cls(path.as_posix(), path)

    def state(self):
        if not self.value.exists():
            raise NodeNotFoundError
        else:
            return str(self.value.stat().st_mtime)


def collect_nodes(session, path, name, nodes):
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


def extract_nodes_from_function_markers(function, parser):
    marker_name = parser.__name__
    for marker in get_marks_from_obj(function, marker_name):
        yield from to_list(parser(*marker.args, **marker.kwargs))
