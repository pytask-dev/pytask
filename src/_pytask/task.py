"""Contain hooks related to the ``@pytask.mark.task`` decorator."""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from _pytask.config import hookimpl
from _pytask.task_utils import COLLECTED_TASKS
from _pytask.task_utils import parse_collected_tasks_with_task_marker

if TYPE_CHECKING:
    from _pytask.report import CollectionReport
    from _pytask.session import Session
    from pathlib import Path


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    config["markers"]["task"] = (
        "Mark a function as a task regardless of its name. Or mark tasks which are "
        "repeated in a loop. See this tutorial for more information: "
        "[link https://bit.ly/3DWrXS3]https://bit.ly/3DWrXS3[/]."
    )


@hookimpl(trylast=True)
def pytask_collect_file(
    session: Session, path: Path, reports: list[CollectionReport]
) -> list[CollectionReport] | None:
    """Collect a file."""
    if (
        any(path.match(pattern) for pattern in session.config["task_files"])
        and COLLECTED_TASKS[path]
    ):
        # Remove tasks from the global to avoid re-collection if programmatic interface
        # is used.
        tasks = COLLECTED_TASKS.pop(path)

        name_to_function = parse_collected_tasks_with_task_marker(tasks)

        collected_reports = []
        for name, function in name_to_function.items():
            report = session.hook.pytask_collect_task_protocol(
                session=session, reports=reports, path=path, name=name, obj=function
            )
            if report is not None:
                collected_reports.append(report)

        return collected_reports
    return None
