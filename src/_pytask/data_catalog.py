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
from attrs import field


__all__ = ["DataCatalog"]


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
        A default node for loading and saving values. By default,
        :class:`~pytask.PickleNode` is used to serialize any Python object with the
        :mod:`pickle` module.
    entries
        A collection of entries in the catalog. Entries can be :class:`~pytask.PNode` or
        a :class:`DataCatalog` itself for nesting catalogs.
    name
        The name of the data catalog. Use it when you are working with multiple data
        catalogs that store data under the same keys.
    path
        A path where automatically created files are stored. By default, it will be
        ``.pytask/data_catalogs/default``.

    """

    default_node: type[PNode] = PickleNode
    entries: dict[str, PNode] = field(factory=dict)
    name: str = "default"
    path: Path | None = None
    _session: Session = field(factory=_create_default_session)
    _instance_path: Path = field(factory=_get_parent_path_of_data_catalog_module)

    def __attrs_post_init__(self) -> None:
        root_path, _ = find_project_root_and_config((self._instance_path,))
        self._session.config["paths"] = (root_path,)

        if not self.path:
            self.path = root_path / ".pytask" / "data_catalogs" / self.name

        self.path.mkdir(parents=True, exist_ok=True)

        self._initialize()

    def _initialize(self) -> None:
        """Initialize the data catalog with persisted nodes from previous runs."""
        for path in self.path.glob("*-node.pkl"):  # type: ignore[union-attr]
            node = pickle.loads(path.read_bytes())  # noqa: S301
            self.entries[node.name] = node

    def __getitem__(self, name: str) -> PNode:
        """Allow to access entries with the squared brackets syntax."""
        if name not in self.entries:
            self.add(name)
        return self.entries[name]

    def add(self, name: str, node: PNode | None = None) -> None:
        """Add an entry to the data catalog."""
        assert isinstance(self.path, Path)

        if not isinstance(name, str):
            msg = "The name of a catalog entry must be a string."
            raise TypeError(msg)

        if node is None:
            filename = str(hashlib.sha256(name.encode()).hexdigest())
            if isinstance(self.default_node, PPathNode):
                self.entries[name] = self.default_node(
                    name=name, path=self.path / f"{filename}.pkl"
                )
            else:
                self.entries[name] = self.default_node(name=name)  # type: ignore[call-arg]
            self.path.joinpath(f"{filename}-node.pkl").write_bytes(
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
            if collected_node is None:  # pragma: no cover
                msg = f"{node!r} cannot be parsed."
                raise NodeNotCollectedError(msg)
            self.entries[name] = collected_node
