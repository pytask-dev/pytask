"""Contains utility functions related to marker.

The utility functions are stored here to be separate from the plugin.

"""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from _pytask.models import CollectionMetadata
from _pytask.node_protocols import PTask


if TYPE_CHECKING:
    from _pytask.mark import Mark


def get_all_marks(obj_or_task: Any | PTask) -> list[Mark]:
    """Get all marks from a callable or task."""
    if isinstance(obj_or_task, PTask):
        marks = obj_or_task.markers
    else:
        obj = obj_or_task
        marks = obj.pytask_meta.markers if hasattr(obj, "pytask_meta") else []
    return marks


def set_marks(obj_or_task: Any | PTask, marks: list[Mark]) -> Any | PTask:
    """Set marks on a callable or task."""
    if isinstance(obj_or_task, PTask):
        obj_or_task.markers = marks
    elif hasattr(obj_or_task, "pytask_meta"):
        obj_or_task.pytask_meta.markers = marks
    else:
        obj_or_task.pytask_meta = CollectionMetadata(markers=marks)
    return obj_or_task


def get_marks(obj_or_task: Any | PTask, marker_name: str) -> list[Mark]:
    """Get marks from callable or task."""
    marks = get_all_marks(obj_or_task)
    return [mark for mark in marks if mark.name == marker_name]


def has_mark(obj_or_task: Any | PTask, marker_name: str) -> bool:
    """Test if callable or task has a certain mark."""
    marks = get_all_marks(obj_or_task)
    return any(mark.name == marker_name for mark in marks)


def remove_marks(
    obj_or_task: Any | PTask, marker_name: str
) -> tuple[Any | PTask, list[Mark]]:
    """Remove marks from callable or task."""
    marks = get_all_marks(obj_or_task)
    selected = [mark for mark in marks if mark.name == marker_name]
    others = [mark for mark in marks if mark.name != marker_name]
    obj_or_task = set_marks(obj_or_task, others)
    return obj_or_task, selected
