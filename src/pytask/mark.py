from _pytest.mark import Mark  # noqa: F401, PT013
from _pytest.mark import MARK_GEN  # noqa: F401, PT013


def get_markers_from_task(task, marker_name):
    return [marker for marker in task.markers if marker.name == marker_name]
