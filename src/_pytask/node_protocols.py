from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Protocol
from typing import runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from _pytask.mark import Mark
    from _pytask.tree_util import PyTree


__all__ = ["PNode", "PPathNode", "PProvisionalNode", "PTask", "PTaskWithPath"]


@runtime_checkable
class PNode(Protocol):
    """Protocol for nodes."""

    name: str

    @property
    def signature(self) -> str:
        """Return the signature of the node."""

    def state(self) -> str | None:
        """Return the state of the node.

        The state can be something like a hash or a last modified timestamp. If the node
        does not exist, you can also return ``None``.

        """

    def load(self, is_product: bool = False) -> Any:
        """Return the value of the node that will be injected into the task.

        Parameters
        ----------
        is_product
            Indicates whether the node is loaded as a dependency or as a product. It can
            be used to return a different value when the node is loaded with a product
            annotation. Then, we usually want to insert the node itself to allow the
            user calling :meth:`PNode.load`.

        """

    def save(self, value: Any) -> Any:
        """Save the value that was returned from a task."""


@runtime_checkable
class PPathNode(PNode, Protocol):
    """Nodes with paths.

    Nodes with paths receive special handling when it comes to printing their names.

    """

    path: Path


@runtime_checkable
class PTask(Protocol):
    """Protocol for nodes."""

    name: str
    depends_on: dict[str, PyTree[PNode | PProvisionalNode]]
    produces: dict[str, PyTree[PNode | PProvisionalNode]]
    function: Callable[..., Any]
    markers: list[Mark]
    report_sections: list[tuple[str, str, str]]
    attributes: dict[Any, Any]

    @property
    def signature(self) -> str:
        """Return the signature of the node."""

    def state(self) -> str | None:
        """Return the state of the node.

        The state can be something like a hash or a last modified timestamp. If the node
        does not exist, you can also return ``None``.

        """

    def execute(self, **kwargs: Any) -> Any:
        """Return the value of the node that will be injected into the task."""


@runtime_checkable
class PTaskWithPath(PTask, Protocol):
    """Tasks with paths.

    Tasks with paths receive special handling when it comes to printing their names.

    """

    path: Path


@runtime_checkable
class PProvisionalNode(Protocol):
    """A protocol for provisional nodes.

    This type of nodes is provisional since it resolves to actual nodes, :class:`PNode`,
    right before a task is executed as a dependency and after the task is executed as a
    product.

    Provisional nodes are nodes that define how the actual nodes look like. They can be
    useful when, for example, a task produces an unknown amount of nodes because it
    downloads some files.

    """

    name: str

    @property
    def signature(self) -> str:
        """Return the signature of the node."""

    def load(self, is_product: bool = False) -> Any:  # pragma: no cover
        """Load a probisional node.

        A provisional node will never be loaded as a dependency since it would be
        collected before.

        It is possible to load a provisional node as a dependency so that it can inject
        basic information about it in the task. For example,
        :meth:`pytask.DirectoryNode.load` injects the root directory.

        """
        if is_product:
            ...
        raise NotImplementedError

    def collect(self) -> list[Any]:
        """Collect the objects that are defined by the provisional nodes."""
