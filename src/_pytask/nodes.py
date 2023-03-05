"""Contains hook implementations for nodes."""
from __future__ import annotations

from typing import Any

from _pytask.config import hookimpl
from _pytask.nodes_utils import FilePathNode
from _pytask.nodes_utils import MetaNode
from _pytask.nodes_utils import Task


@hookimpl
def pytask_node_exists(node: MetaNode) -> bool | None:
    """Check if a task or node on the filesystem exist."""
    if isinstance(node, (Task, FilePathNode)):
        return node.path.exists()
    return None


@hookimpl
def pytask_node_state(node: MetaNode) -> Any | None:
    """Return the state of a task or file path node."""
    if isinstance(node, (Task, FilePathNode)) and node.path.exists():
        return str(node.path.stat().st_mtime)
    return None
