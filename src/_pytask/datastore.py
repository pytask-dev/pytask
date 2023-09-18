"""Contains the implementation of a datastore.

The datastore is an abstraction layer between users and nodes.

"""
from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from attrs import define
from attrs import Factory

if TYPE_CHECKING:
    from _pytask.node_protocols import PNode


__all__ = ["DataStore", "PickleNode"]


@define
class DataStore:
    directory: Path = Path.cwd().joinpath(".pytask").resolve()
    nodes: dict[str, PNode] = Factory(dict)

    def __getitem__(self, name: str) -> PNode:
        if name not in self.nodes:
            self.add(name)
        return self.nodes[name]

    def add(self, name: str, node: PNode | None = None) -> None:
        if not isinstance(name, str):
            msg = "The name of a datastore entry must be a string."
            raise TypeError(msg)

        if name in self.nodes:
            msg = f"There is already an entry with the name {name!r} in the datastore."
            raise ValueError(msg)

        if node is None:
            filename = str(hashlib.sha256(name.encode()).hexdigest())
            self.nodes[name] = PickleNode(
                name=name, path=self.directory / f"{filename}.pkl"
            )
        else:
            self.nodes[name] = node


@define
class PickleNode:
    name: str
    path: Path

    def state(self) -> str | None:
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def load(self) -> Any:
        return pickle.loads(self.path.read_bytes())  # noqa: S301

    def save(self, value: Any) -> None:
        self.path.write_bytes(pickle.dumps(value))
