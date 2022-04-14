"""This module contain hooks related to the ``@pytask.mark.task`` decorator."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from _pytask.config import hookimpl
from _pytask.mark_utils import has_mark
from _pytask.report import CollectionReport
from _pytask.session import Session
from _pytask.task_utils import COLLECTED_TASKS
from _pytask.task_utils import parse_collected_tasks_with_task_marker


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
            session.hook.pytask_parametrize_kwarg_to_marker(
                obj=function,
                kwargs=function.pytask_meta.kwargs,  # type: ignore[attr-defined]
            )

            if has_mark(function, "parametrize"):
                names_and_objects = session.hook.pytask_parametrize_task(
                    session=session, name=name, obj=function
                )
            else:
                names_and_objects = [(name, function)]

            for name_, obj_ in names_and_objects:
                report = session.hook.pytask_collect_task_protocol(
                    session=session, reports=reports, path=path, name=name_, obj=obj_
                )
                if report is not None:
                    collected_reports.append(report)

        return collected_reports
    else:
        return None
