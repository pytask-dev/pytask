"""Shared task invocation and return-product handling."""

from __future__ import annotations

import inspect
from typing import Any

from _pytask.exceptions import NodeLoadError
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import PTask
from _pytask.tree_util import tree_leaves
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_structure


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


def save_return_products(task: PTask, out: Any) -> None:
    """Validate the return structure and save its declared products."""
    if "return" in task.produces:
        structure_out = tree_structure(out)
        structure_return = tree_structure(task.produces["return"])

        # strict must be false when none is leaf.
        if not structure_return.is_prefix(structure_out, strict=False):
            msg = (
                f"The structure of the return annotation is not a subtree of the "
                f"structure of the function return.\n\nFunction return: {structure_out}"
                f"\n\nReturn annotation: {structure_return}"
            )
            raise ValueError(msg)

        nodes = tree_leaves(task.produces["return"])
        values = structure_return.flatten_up_to(out)
        for node, value in zip(nodes, values, strict=False):
            if not isinstance(node, PProvisionalNode):
                node.save(value)
