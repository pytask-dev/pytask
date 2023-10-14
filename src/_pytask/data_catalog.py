"""Contains the implementation of a data catalog.

The data catalog is an abstraction layer between users and nodes.

"""
from __future__ import annotations

import hashlib
import pickle
from typing import TYPE_CHECKING

from _pytask.config_utils import find_project_root_and_config
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.nodes import PickleNode
from attrs import define
from attrs import Factory

if TYPE_CHECKING:
    from pathlib import Path


__all__ = ["DataCatalog"]


def _find_directory() -> Path:
    root_path, _ = find_project_root_and_config(None)
    return root_path.joinpath(".pytask", "data_catalogs")


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
        A collection of entries in the catalog. Entries can be :class:`pytask.PNode` or
        a :class:`DataCatalog` itself for nesting catalogs.
    name
        The name of the data catalog. Use it when you are working with multiple data
        catalogs that store data under the same keys.

    """

    default_node: type[PNode] = PickleNode
    directory: Path | None = None
    entries: dict[str, DataCatalog | PNode] = Factory(dict)
    name: str = "default"

    def __attrs_post_init__(self) -> None:
        if not self.directory:
            root = _find_directory()
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
        if not isinstance(name, str):
            msg = "The name of a catalog entry must be a string."
            raise TypeError(msg)

        if name in self.entries:
            msg = (
                f"There is already an entry with the name {name!r} in the data catalog."
            )
            raise ValueError(msg)

        if node is None:
            filename = str(hashlib.sha256(name.encode()).hexdigest())
            if isinstance(self.default_node, PPathNode):
                self.entries[name] = self.default_node(
                    name=name, path=self.directory / f"{filename}.pkl"
                )
            else:
                self.entries[name] = self.default_node(name=name)  # type: ignore[call-arg]
            self.directory.joinpath(f"{filename}-node.pkl").write_bytes(  # type: ignore[union-attr]
                pickle.dumps(self.entries[name])
            )
        else:
            self.entries[name] = node
