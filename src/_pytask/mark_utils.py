"""This module contains utility functions related to marker.

The utility functions are stored here to be separate from the plugin.

"""


def get_specific_markers_from_task(task, marker_name):
    """Get a specific group of markers from a task."""
    return [marker for marker in task.markers if marker.name == marker_name]


def get_marks_from_obj(obj, marker_name):
    """Get a specific group of markers from a task function."""
    return [
        marker
        for marker in getattr(obj, "pytaskmark", [])
        if marker.name == marker_name
    ]


def has_marker(obj, marker_name):
    """Determine whether a task function has a certain marker."""
    return any(marker.name == marker_name for marker in getattr(obj, "pytaskmark", []))
