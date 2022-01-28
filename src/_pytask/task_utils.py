from typing import Any
from typing import Callable
from typing import Optional

from _pytask.mark import Mark
from _pytask.mark_utils import remove_markers_from_func


def task(name: Optional[str] = None) -> str:
    return name


def parse_task_marker(obj: Callable[..., Any]) -> str:
    obj, task_markers = remove_markers_from_func(obj, "task")

    if len(task_markers) != 1:
        raise ValueError(
            "The @pytask.mark.task decorator cannot be applied more than once to a "
            "single task."
        )
    task_marker = task_markers[0]

    name = task(*task_marker.args, **task_marker.kwargs)

    obj.pytaskmark.append(Mark("task", (), {}))  # type: ignore[attr-defined]

    return name
