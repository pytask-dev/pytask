"""Contains the implementation of a data catalog.

The data catalog is an abstraction layer between users and nodes.

"""

from __future__ import annotations

import hashlib
import inspect
import pickle
import re
from pathlib import Path
from typing import Any

from attrs import define
from attrs import field

from _pytask.config_utils import find_project_root_and_config
from _pytask.exceptions import NodeNotCollectedError
from _pytask.models import NodeInfo
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.nodes import PickleNode
from _pytask.pluginmanager import storage
from _pytask.session import Session

__all__ = ["DataCatalog"]


def _get_parent_path_of_data_catalog_module(stacklevel: int = 2) -> Path:
    """Get the parent path of the module where the data catalog is defined."""
    stack = inspect.stack()
    potential_path = stack[stacklevel].frame.f_globals.get("__file__")
    if potential_path:
        return Path(potential_path).parent
    return Path.cwd()


@define(kw_only=True)
class DataCatalog:
    """A data catalog.

    Parameters
    ----------
    default_node
        A default node for loading and saving values. By default,
        :class:`~pytask.PickleNode` is used to serialize any Python object with the
        :mod:`pickle` module.
    name
        The name of the data catalog which can only contain letters, numbers, hyphens
        and underscores. Use it when you are working with multiple data catalogs to
        store data in different locations.
    path
        A path where automatically created files are stored. By default, it will be
        ``.pytask/data_catalogs/default``.

    """

    default_node: type[PNode] = PickleNode
    name: str = field(default="default")
    path: Path | None = None
    _entries: dict[str, PNode | PProvisionalNode] = field(factory=dict)
    _instance_path: Path = field(factory=_get_parent_path_of_data_catalog_module)
    _session_config: dict[str, Any] = field(
        factory=lambda *x: {"check_casing_of_paths": True}  # noqa: ARG005
    )

    @name.validator
    def _check(self, attribute: str, value: str) -> None:  # noqa: ARG002
        _rich_traceback_omit = True
        if not isinstance(value, str):
            msg = "The name of a data catalog must be a string."
            raise TypeError(msg)
        if not re.match(r"[a-zA-Z0-9-_]+", value):
            msg = (
                "The name of a data catalog must be a string containing only letters, "
                "numbers, hyphens, and underscores."
            )
            raise ValueError(msg)

    def __attrs_post_init__(self) -> None:
        root_path, _ = find_project_root_and_config((self._instance_path,))
        self._session_config["paths"] = (root_path,)

        if not self.path:
            self.path = root_path / ".pytask" / "data_catalogs" / self.name

        self.path.mkdir(parents=True, exist_ok=True)

        # Initialize the data catalog with persisted nodes from previous runs.
        for path in self.path.glob("*-node.pkl"):
            node = pickle.loads(path.read_bytes())  # noqa: S301
            self._entries[node.name] = node

    def __getitem__(self, name: str) -> PNode | PProvisionalNode:
        """Allow to access entries with the squared brackets syntax."""
        if name not in self._entries:
            self.add(name)
        return self._entries[name]

    def add(self, name: str, node: PNode | PProvisionalNode | Any = None) -> None:
        """Add an entry to the data catalog."""
        if not isinstance(name, str):
            msg = "The name of a catalog entry must be a string."
            raise TypeError(msg)

        if node is None:
            filename = hashlib.sha256(name.encode()).hexdigest()
            if isinstance(self.default_node, PPathNode):
                self._entries[name] = self.default_node(
                    name=name, path=self.path / f"{filename}.pkl"
                )
            else:
                self._entries[name] = self.default_node(name=name)  # type: ignore[call-arg]
            self.path.joinpath(f"{filename}-node.pkl").write_bytes(  # type: ignore[union-attr]
                pickle.dumps(self._entries[name])
            )
        elif isinstance(node, (PNode, PProvisionalNode)):
            self._entries[name] = node
        else:
            # Acquire the latest pluginmanager.
            session = Session(config=self._session_config, hook=storage.get().hook)
            collected_node = session.hook.pytask_collect_node(
                session=session,
                path=self._instance_path,
                node_info=NodeInfo(
                    arg_name=name, path=(), value=node, task_path=None, task_name=""
                ),
            )
            if collected_node is None:  # pragma: no cover
                msg = f"{node!r} cannot be parsed."
                raise NodeNotCollectedError(msg)
            self._entries[name] = collected_node
