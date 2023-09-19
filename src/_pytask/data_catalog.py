"""Contains the implementation of a data catalog.

The data catalog is an abstraction layer between users and nodes.

"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from _pytask.nodes import PickleNode
from attrs import define
from attrs import Factory

if TYPE_CHECKING:
    from _pytask.node_protocols import PNode


__all__ = ["DataCatalog"]


@define
class DataCatalog:
    """A data catalog.

    Parameters
    ----------
    directory
        A directory where automatically created files are stored.
    entries
        A collection of entries in the catalog. Entries can be :class:`pytask.PNode` or
        a :class:`DataCatalog` itself for nesting catalogs.

    """

    directory: Path = Factory(lambda *x: Path.cwd().joinpath(".pytask").resolve())
    entries: dict[str, DataCatalog | PNode] = Factory(dict)

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
            self.entries[name] = PickleNode(
                name=name, path=self.directory / f"{filename}.pkl"
            )
        else:
            self.entries[name] = node
