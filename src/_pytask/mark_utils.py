"""This module contains utility functions related to marker.

The utility functions are stored here to be separate from the plugin.

"""
from typing import Any
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from _pytask.nodes import MetaTask
    from _pytask.mark import Mark


def get_specific_markers_from_task(task: "MetaTask", marker_name: str) -> "List[Mark]":
    """Get a specific group of markers from a task."""
    return [marker for marker in task.markers if marker.name == marker_name]


def get_marks_from_obj(obj: Any, marker_name: str) -> "List[Mark]":
    """Get a specific group of markers from a task function."""
    return [
        marker
        for marker in getattr(obj, "pytaskmark", [])
        if marker.name == marker_name
    ]


def has_marker(obj: Any, marker_name: str) -> bool:
    """Determine whether a task function has a certain marker."""
    return any(marker.name == marker_name for marker in getattr(obj, "pytaskmark", []))


def remove_markers_from_func(obj: Any, marker_name: str) -> Tuple[Any, List["Mark"]]:
    """Remove parametrize markers from the object."""
    markers = [i for i in getattr(obj, "pytaskmark", []) if i.name == marker_name]
    others = [i for i in getattr(obj, "pytaskmark", []) if i.name != marker_name]
    obj.pytaskmark = others

    return obj, markers
