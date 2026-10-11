"""Typed operations on the recursive trees used for task inputs and outputs."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar
from typing import cast

from _pytask.node_protocols import NodeTree
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import TaskIO
from _pytask.node_protocols import TaskNode
from _pytask.tree_util import PyTree
from _pytask.tree_util import _pytree

if TYPE_CHECKING:
    from collections.abc import Callable

_T = TypeVar("_T")


def task_node_leaves(tree: NodeTree | TaskIO) -> list[TaskNode]:
    """Flatten a task tree while retaining its node leaf type."""
    # optree's dynamic PyTree alias cannot express pytask's static recursive alias.
    return cast("list[TaskNode]", _pytree.leaves(cast("Any", tree), none_is_leaf=True))


def concrete_product_nodes(products: TaskIO) -> list[PNode]:
    """Return products after provisional products have been collected."""
    nodes: list[PNode] = []
    for node in task_node_leaves(products):
        if isinstance(node, PProvisionalNode) or not isinstance(node, PNode):
            msg = f"Uncollected provisional product: {node!r}"
            raise TypeError(msg)
        nodes.append(node)
    return nodes


def map_task_io(
    func: Callable[[tuple[Any, ...], TaskNode], _T],
    tree: TaskIO,
) -> dict[str, PyTree[_T]]:
    """Map task nodes while preserving the top-level argument mapping."""
    # optree preserves the dict root and recursively replaces each leaf.
    return cast(
        "dict[str, PyTree[_T]]",
        _pytree.map_with_path(func, cast("Any", tree), none_is_leaf=True),
    )
