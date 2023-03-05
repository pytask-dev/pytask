"""Contains hook implementations for nodes."""
from __future__ import annotations

from typing import Any

from _pytask.config import hookimpl
from _pytask.nodes_utils import FilePathNode
from _pytask.nodes_utils import Node
from _pytask.nodes_utils import Task


@hookimpl
def pytask_node_state(node: Node) -> Any | None:
    """Return the state of a task or file path node."""
    if isinstance(node, (Task, FilePathNode)) and node.path.exists():
        return str(node.path.stat().st_mtime)
    return None
