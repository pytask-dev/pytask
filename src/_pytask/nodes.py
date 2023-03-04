"""Contains hook implementations for nodes."""
from __future__ import annotations

from typing import Any

from _pytask.config import hookimpl
from _pytask.nodes_utils import FilePathNode
from _pytask.nodes_utils import MetaNode
from _pytask.nodes_utils import Task


@hookimpl
def pytask_node_exists(node: MetaNode) -> bool | None:
    if isinstance(node, (Task, FilePathNode)):
        return node.path.exists()
    return None


@hookimpl
def pytask_node_state(node: MetaNode) -> Any | None:
    if isinstance(node, (Task, FilePathNode)) and node.path.exists():
        return str(node.path.stat().st_mtime)
    return None
