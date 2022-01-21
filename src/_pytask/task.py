from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional

from _pytask.config import hookimpl
from _pytask.mark_utils import has_marker
from _pytask.nodes import PythonFunctionTask
from _pytask.session import Session
from _pytask.task_utils import parse_task_marker


@hookimpl
def pytask_parse_config(config: Dict[str, Any]) -> None:
    config["markers"]["task"] = "Mark a function as a task regardless of its name."


@hookimpl
def pytask_collect_task(
    session: Session, path: Path, name: str, obj: Any
) -> Optional[PythonFunctionTask]:
    """Collect a task which is a function.

    There is some discussion on how to detect functions in this `thread
    <https://stackoverflow.com/q/624926/7523785>`_. :class:`types.FunctionType` does not
    detect built-ins which is not possible anyway.

    """
    if has_marker(obj, "task") and callable(obj):
        parsed_name = parse_task_marker(obj)
        if parsed_name is not None:
            name = parsed_name
        return PythonFunctionTask.from_path_name_function_session(
            path, name, obj, session
        )
    else:
        return None
