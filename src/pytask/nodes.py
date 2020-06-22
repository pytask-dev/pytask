import functools
import inspect
from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path

import attr
from pytask.exceptions import NodeNotCollectedError
from pytask.exceptions import NodeNotFoundError
from pytask.shared import to_list


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
    session = attr.ib()
    markers = attr.ib()

    @classmethod
    def from_path_name_function_session(cls, path, name, function, session):
        depends_on_nodes = extract_nodes_from_function_markers(function, "depends_on")
        depends_on = collect_nodes(session, path, name, depends_on_nodes)

        produces_nodes = extract_nodes_from_function_markers(function, "produces")
        produces = collect_nodes(session, path, name, produces_nodes)

        markers = [
            marker
            for marker in getattr(function, "pytestmark", [])
            if marker.name not in ["depends_on", "produces"]
        ]

        return cls(
            path=path,
            name=name,
            function=function,
            depends_on=depends_on,
            produces=produces,
            session=session,
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
                self.depends_on[0].original_value
                if len(self.depends_on) == 1
                else [node.original_value for node in self.depends_on]
            )
        if "produces" in func_arg_names:
            kwargs["produces"] = (
                self.produces[0].original_value
                if len(self.produces) == 1
                else [node.original_value for node in self.produces]
            )

        return kwargs


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes.

    Attributes
    ----------
    name : str
        Name of the node which makes it identifiable in the DAG.
    original_value : any
        Original value passed to the decorator which can be requested inside the
        function.

    """

    @abstractmethod
    def state(self):
        pass


@attr.s
class FilePathNode(MetaNode):
    name = attr.ib()
    path = attr.ib()
    original_value = attr.ib()

    @classmethod
    @functools.lru_cache()
    def from_path_and_original_value(cls, path, original_value):
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        return cls(path.as_posix(), path, path)

    def state(self):
        if not self.path.exists():
            raise NodeNotFoundError
        else:
            return str(self.path.stat().st_mtime)


def collect_nodes(session, path, name, nodes):
    collect_nodes = []
    for node in nodes:
        collected_node = session.hook.pytask_collect_node(path=path, node=node)
        if collected_node is None:
            raise NodeNotCollectedError(
                f"'{node}' could not be collected from path '{path}' and task '{name}'."
            )
        else:
            collect_nodes.append(collected_node)

    return collect_nodes


def extract_nodes_from_function_markers(function, marker_name):
    for marker in getattr(function, "pytestmark", []):
        for args in marker.args:
            for arg in to_list(args):
                if marker.name == marker_name:
                    yield arg
