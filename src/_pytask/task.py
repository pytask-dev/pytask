"""Contain hooks related to the :func:`@task <pytask.task>`."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from _pytask.console import format_strings_as_flat_tree
from _pytask.pluginmanager import hookimpl
from _pytask.shared import find_duplicates
from _pytask.task_utils import COLLECTED_TASKS
from _pytask.task_utils import parse_collected_tasks_with_task_marker

if TYPE_CHECKING:
    from pathlib import Path

    from _pytask.reports import CollectionReport
    from _pytask.session import Session


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

        _raise_error_when_task_functions_are_duplicated(tasks)

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


def _raise_error_when_task_functions_are_duplicated(
    tasks: list[Callable[..., Any]],
) -> None:
    """Raise error when task functions are duplicated.

    When task functions are created outside the loop body, every wrapped version of the

    """
    duplicates = find_duplicates(tasks)
    if not duplicates:
        return

    strings = [
        f"function_name={func.pytask_meta.name}, id={func.pytask_meta.id_}"
        for func in duplicates
    ]
    flat_tree = format_strings_as_flat_tree(strings, "Duplicated tasks")
    msg = (
        "There are some duplicates among the repeated tasks. It happens when you define"
        "the task function outside the loop body and merely wrap in the loop body with "
        "the 'task(...)(func)' decorator. As a workaround, wrap the task function in "
        f"a lambda expression like 'task(...)(lambda **x: func(**x))'.\n\n{flat_tree}"
    )
    raise ValueError(msg)


@hookimpl
def pytask_unconfigure() -> None:
    COLLECTED_TASKS.clear()
