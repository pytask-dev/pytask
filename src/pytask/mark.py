from _pytest.mark import MARK_GEN  # noqa: F401, PT013


def get_markers_from_task(task, marker_name):
    markers = getattr(task.function, "pytestmark", [])
    return [marker for marker in markers if marker.name == marker_name]
