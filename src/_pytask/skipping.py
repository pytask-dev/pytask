"""This module contains everything related to skipping tasks."""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from _pytask.config import hookimpl
from _pytask.dag import descending_tasks
from _pytask.mark import Mark
from _pytask.mark_utils import get_specific_markers_from_task
from _pytask.outcomes import Skipped
from _pytask.outcomes import SkippedAncestorFailed
from _pytask.outcomes import SkippedUnchanged
from _pytask.outcomes import TaskOutcome
from _pytask.traceback import remove_traceback_from_exc_info


if TYPE_CHECKING:
    from _pytask.session import Session
    from _pytask.nodes import MetaTask
    from _pytask.report import ExecutionReport


def skip_ancestor_failed(reason: str = "No reason provided.") -> str:
    """Function to parse information in ``@pytask.mark.skip_ancestor_failed``."""
    return reason


def skipif(condition: bool, *, reason: str) -> tuple[bool, str]:
    """Function to parse information in ``@pytask.mark.skipif``."""
    return condition, reason


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    markers = {
        "skip": "Skip a task and all its subsequent tasks as well.",
        "skip_ancestor_failed": "Internal decorator applied to tasks whose ancestor "
        "failed.",
        "skip_unchanged": "Internal decorator applied to tasks which have already been "
        "executed and have not been changed.",
        "skipif": "Skip a task and all its subsequent tasks in case a condition is "
        "fulfilled.",
    }
    config["markers"] = {**config["markers"], **markers}


@hookimpl
def pytask_execute_task_setup(task: MetaTask) -> None:
    """Take a short-cut for skipped tasks during setup with an exception."""
    markers = get_specific_markers_from_task(task, "skip_unchanged")
    if markers:
        raise SkippedUnchanged

    markers = get_specific_markers_from_task(task, "skip_ancestor_failed")
    if markers:
        message = "\n".join(
            skip_ancestor_failed(*marker.args, **marker.kwargs) for marker in markers
        )
        raise SkippedAncestorFailed(message)

    markers = get_specific_markers_from_task(task, "skip")
    if markers:
        raise Skipped

    markers = get_specific_markers_from_task(task, "skipif")
    if markers:
        marker_args = [skipif(*marker.args, **marker.kwargs) for marker in markers]
        message = "\n".join(arg[1] for arg in marker_args if arg[0])
        should_skip = any(arg[0] for arg in marker_args)
        if should_skip:
            raise Skipped(message)


@hookimpl
def pytask_execute_task_process_report(
    session: Session, report: ExecutionReport
) -> bool | None:
    """Process the execution reports for skipped tasks.

    This functions allows to turn skipped tasks to successful tasks.

    """
    task = report.task

    if report.exc_info:
        if isinstance(report.exc_info[1], SkippedUnchanged):
            report.outcome = TaskOutcome.SKIP_UNCHANGED

        elif isinstance(report.exc_info[1], Skipped):
            report.outcome = TaskOutcome.SKIP

            for descending_task_name in descending_tasks(task.name, session.dag):
                descending_task = session.dag.nodes[descending_task_name]["task"]
                descending_task.markers.append(
                    Mark(
                        "skip",
                        (),
                        {"reason": f"Previous task {task.name!r} was skipped."},
                    )
                )

        elif isinstance(report.exc_info[1], SkippedAncestorFailed):
            report.outcome = TaskOutcome.SKIP_PREVIOUS_FAILED
            report.exc_info = remove_traceback_from_exc_info(report.exc_info)

    if report.exc_info and isinstance(
        report.exc_info[1], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
    ):
        return True
    else:
        return None
