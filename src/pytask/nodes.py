import functools
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
        self.function()

    def state(self):
        return str(self.path.stat().st_mtime)


class MetaNode(metaclass=ABCMeta):
    @abstractmethod
    def state(self):
        pass


@attr.s
class FilePathNode(MetaNode):
    name = attr.ib()
    path = attr.ib()

    @classmethod
    @functools.lru_cache()
    def from_path(cls, path):
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        return cls(path.name, path)

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
