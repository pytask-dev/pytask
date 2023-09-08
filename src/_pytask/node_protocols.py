from __future__ import annotations

from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import Protocol
from typing import runtime_checkable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from _pytask.tree_util import PyTree
    from pathlib import Path
    from _pytask.mark import Mark


__all__ = ["MetaNode", "PNode", "PPathNode", "PTask", "PTaskWithPath"]


@runtime_checkable
class MetaNode(Protocol):
    """Protocol for an intersection between nodes and tasks."""

    name: str
    """The name of node that must be unique."""

    @abstractmethod
    def state(self) -> str | None:
        """Return the state of the node.

        The state can be something like a hash or a last modified timestamp. If the node
        does not exist, you can also return ``None``.

        """
        ...


@runtime_checkable
class PNode(MetaNode, Protocol):
    """Protocol for nodes."""

    def load(self) -> Any:
        """Return the value of the node that will be injected into the task."""
        ...

    def save(self, value: Any) -> Any:
        """Save the value that was returned from a task."""
        ...


@runtime_checkable
class PPathNode(PNode, Protocol):
    """Nodes with paths.

    Nodes with paths receive special handling when it comes to printing their names.

    """

    path: Path


@runtime_checkable
class PTask(MetaNode, Protocol):
    """Protocol for nodes."""

    name: str
    depends_on: PyTree[PNode]
    produces: PyTree[PNode]
    markers: list[Mark]
    report_sections: list[tuple[str, str, str]]
    attributes: dict[Any, Any]
    function: Callable[..., Any]

    def execute(self, **kwargs: Any) -> Any:
        """Return the value of the node that will be injected into the task."""
        ...


@runtime_checkable
class PTaskWithPath(PTask, Protocol):
    """Tasks with paths.

    Tasks with paths receive special handling when it comes to printing their names.

    """

    path: Path
