def get_specific_markers_from_task(task, marker_name):
    return [marker for marker in task.markers if marker.name == marker_name]


def get_marks_from_obj(obj, marker_name):
    return [
        marker
        for marker in getattr(obj, "pytaskmark", [])
        if marker.name == marker_name
    ]


def has_marker(obj, marker_name):
    return any(marker.name == marker_name for marker in getattr(obj, "pytaskmark", []))
