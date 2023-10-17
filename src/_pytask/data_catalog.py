"""Contains the implementation of a data catalog.

The data catalog is an abstraction layer between users and nodes.

"""
from __future__ import annotations

import hashlib
import inspect
import pickle
from pathlib import Path

from _pytask.config_utils import find_project_root_and_config
from _pytask.exceptions import NodeNotCollectedError
from _pytask.models import NodeInfo
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.nodes import PickleNode
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from attrs import define
from attrs import Factory


__all__ = ["DataCatalog"]


def _find_directory(path: Path) -> Path:
    """Find directory where data catalog can store its data."""
    root_path, _ = find_project_root_and_config([path])
    return root_path.joinpath(".pytask", "data_catalogs")


def _get_parent_path_of_data_catalog_module(stacklevel: int = 2) -> Path:
    """Get the parent path of the module where the data catalog is defined."""
    stack = inspect.stack()
    potential_path = stack[stacklevel].frame.f_globals.get("__file__")
    if potential_path:
        return Path(potential_path).parent
    return Path.cwd()


def _create_default_session() -> Session:
    """Create a default session to use the hooks and collect nodes."""
    return Session(
        config={"check_casing_of_paths": True}, hook=get_plugin_manager().hook
    )


@define(kw_only=True)
class DataCatalog:
    """A data catalog.

    Parameters
    ----------
    default_node
        A default node for loading and saving values.
    directory
        A directory where automatically created files are stored.
    entries
        A collection of entries in the catalog. Entries can be :class:`~pytask.PNode` or
        a :class:`DataCatalog` itself for nesting catalogs.
    name
        The name of the data catalog. Use it when you are working with multiple data
        catalogs that store data under the same keys.

    """

    default_node: type[PNode] = PickleNode
    directory: Path | None = None
    entries: dict[str, DataCatalog | PNode] = Factory(dict)
    name: str = "default"
    _session: Session = Factory(_create_default_session)
    _instance_path: Path = Factory(_get_parent_path_of_data_catalog_module)

    def __attrs_post_init__(self) -> None:
        if not self.directory:
            root = _find_directory(self._instance_path)
            self.directory = root / self.name
            self.directory.mkdir(parents=True, exist_ok=True)

        self._initialize()

    def _initialize(self) -> None:
        """Initialize the data catalog with persisted nodes from previous runs."""
        for path in self.directory.glob("*-node.pkl"):  # type: ignore[union-attr]
            node = pickle.loads(path.read_bytes())  # noqa: S301
            self.entries[node.name] = node

    def __getitem__(self, name: str) -> DataCatalog | PNode:
        """Allow to access entries with the squared brackets syntax."""
        if name not in self.entries:
            self.add(name)
        return self.entries[name]

    def add(self, name: str, node: DataCatalog | PNode | None = None) -> None:
        """Add an entry to the data catalog."""
        assert isinstance(self.directory, Path)

        if not isinstance(name, str):
            msg = "The name of a catalog entry must be a string."
            raise TypeError(msg)

        if node is None:
            filename = str(hashlib.sha256(name.encode()).hexdigest())
            if isinstance(self.default_node, PPathNode):
                self.entries[name] = self.default_node(
                    name=name, path=self.directory / f"{filename}.pkl"
                )
            else:
                self.entries[name] = self.default_node(name=name)  # type: ignore[call-arg]
            self.directory.joinpath(f"{filename}-node.pkl").write_bytes(
                pickle.dumps(self.entries[name])
            )
        elif isinstance(node, PNode):
            self.entries[name] = node
        else:
            collected_node = self._session.hook.pytask_collect_node(
                session=self._session,
                path=self._instance_path,
                node_info=NodeInfo(
                    arg_name=name, path=(), value=node, task_path=None, task_name=""
                ),
            )
            if collected_node is None:
                msg = f"{node!r} cannot be parsed."
                raise NodeNotCollectedError(msg)
            self.entries[name] = collected_node