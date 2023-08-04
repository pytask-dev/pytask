from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Protocol
from typing import runtime_checkable


@runtime_checkable
class MetaNode(Protocol):
    """Protocol for an intersection between nodes and tasks."""

    name: str | None
    """The name of node that must be unique."""

    @abstractmethod
    def state(self) -> Any:
        ...


@runtime_checkable
class Node(MetaNode, Protocol):
    """Protocol for nodes."""

    value: Any

    def load(self) -> Any:
        ...

    def save(self, value: Any) -> Any:
        ...

    def set_value(self, value: Any) -> Any:
        ...


@runtime_checkable
class PPathNode(Node, Protocol):
    """Nodes with paths."""

    path: Path
