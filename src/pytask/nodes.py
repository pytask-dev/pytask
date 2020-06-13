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

    @classmethod
    def from_path_name_function_session(cls, path, name, function, session):
        depends_on = []
        for node in extract_nodes_from_mark(function, "depends_on"):
            collected_node = session.hook.pytask_collect_node(path=path, node=node)
            if collected_node is None:
                raise NodeNotCollectedError(
                    f"Dependency {node} could not be collected from path {path} and "
                    f"function {name}."
                )
            else:
                depends_on.append(collected_node)

        produces = []
        for node in extract_nodes_from_mark(function, "produces"):
            collected_node = session.hook.pytask_collect_node(path=path, node=node)
            if collected_node is None:
                raise NodeNotCollectedError(
                    f"Product {node} could not be collected from path {path} and "
                    f"function {name}."
                )
            else:
                produces.append(collected_node)

        return cls(
            path=path,
            name=name,
            function=function,
            depends_on=depends_on,
            produces=produces,
            session=session,
        )

    def execute(self):
        self.session.hook.pytask_execute_task_pyfunc(function=self.function)

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


def extract_nodes_from_mark(function, marker_name):
    for marker in getattr(function, "pytestmark", []):
        for args in marker.args:
            for arg in to_list(args):
                if marker.name == marker_name:
                    yield arg
