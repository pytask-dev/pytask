"""This module contains utility functions related to marker.

The utility functions are stored here to be separate from the plugin.

"""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from _pytask.nodes import Task
    from _pytask.mark import Mark


def get_specific_markers_from_task(task: Task, marker_name: str) -> list[Mark]:
    """Get a specific group of markers from a task."""
    return [marker for marker in task.markers if marker.name == marker_name]


def get_marks_from_obj(obj: Any, marker_name: str) -> list[Mark]:
    """Get a specific group of markers from a task function."""
    markers = obj.pytask_meta.markers if hasattr(obj, "pytask_meta") else []
    return [marker for marker in markers if marker.name == marker_name]


def has_marker(obj: Any, marker_name: str) -> bool:
    """Determine whether a task function has a certain marker."""
    markers = obj.pytask_meta.markers if hasattr(obj, "pytask_meta") else []
    return any(marker.name == marker_name for marker in markers)


def remove_markers_from_func(obj: Any, marker_name: str) -> tuple[Any, list[Mark]]:
    """Remove parametrize markers from the object."""
    if hasattr(obj, "pytask_meta"):
        markers = obj.pytask_meta.markers
        selected = [i for i in markers if i.name == marker_name]
        others = [i for i in markers if i.name != marker_name]
        obj.pytask_meta.markers = others
    else:
        selected = []
    return obj, selected
