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
    def state(self) -> str | None:
        """Return the state of the node.

        The state can be something like a hash or a last modified timestamp. If the node
        does not exist, you can also return ``None``.

        """
        ...


@runtime_checkable
class Node(MetaNode, Protocol):
    """Protocol for nodes."""

    value: Any

    def load(self) -> Any:
        """Return the value of the node that will be injected into the task."""
        ...

    def save(self, value: Any) -> Any:
        """Save the value that was returned from a task."""
        ...

    def from_annot(self, value: Any) -> Any:
        """Complete the node by setting the value from an default argument.

        Use it, if you want to add information on how a node handles an argument while
        keeping the type of the value unrelated to pytask.

        .. codeblock: python

            def task_example(value: Annotated[Any, PythonNode(hash=True)], produces):
                ...


        """
        ...


@runtime_checkable
class PPathNode(Node, Protocol):
    """Nodes with paths.

    Nodes with paths receive special handling when it comes to printing their names.

    """

    path: Path
