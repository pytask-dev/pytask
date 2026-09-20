"""Shared task invocation and return-product handling."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING
from typing import Any

from _pytask.exceptions import NodeLoadError
from _pytask.tree_util import tree_map

if TYPE_CHECKING:
    from _pytask.node_protocols import PNode
    from _pytask.node_protocols import PProvisionalNode
    from _pytask.node_protocols import PTask


def _safe_load(node: PNode | PProvisionalNode, task: PTask, *, is_product: bool) -> Any:
    try:
        return node.load(is_product=is_product)
    except Exception as e:
        msg = f"Exception while loading node {node.name!r} of task {task.name!r}"
        raise NodeLoadError(msg) from e


def execute_task(task: PTask) -> Any:
    """Load task arguments and invoke its body once."""
    parameters = inspect.signature(task.function).parameters

    kwargs = {}
    for name, value in task.depends_on.items():
        kwargs[name] = tree_map(lambda x: _safe_load(x, task, is_product=False), value)

    for name, value in task.produces.items():
        if name in parameters:
            kwargs[name] = tree_map(
                lambda x: _safe_load(x, task, is_product=True), value
            )

    return task.execute(**kwargs)
