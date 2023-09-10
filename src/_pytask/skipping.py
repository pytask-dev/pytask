"""Contains everything related to skipping tasks."""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from _pytask.config import hookimpl
from _pytask.dag_utils import descending_tasks
from _pytask.mark import Mark
from _pytask.mark_utils import get_marks
from _pytask.mark_utils import has_mark
from _pytask.outcomes import Skipped
from _pytask.outcomes import SkippedAncestorFailed
from _pytask.outcomes import SkippedUnchanged
from _pytask.outcomes import TaskOutcome
from _pytask.traceback import remove_traceback_from_exc_info


if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from _pytask.session import Session
    from _pytask.report import ExecutionReport


def skip_ancestor_failed(reason: str = "No reason provided.") -> str:
    """Function to parse information in ``@pytask.mark.skip_ancestor_failed``."""
    return reason


def skipif(condition: bool, *, reason: str) -> tuple[bool, str]:
    """Function to parse information in ``@pytask.mark.skipif``."""
    return condition, reason


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    markers = {
        "skip": "Skip a task and all its dependent tasks.",
        "skip_ancestor_failed": "Internal decorator applied to tasks if any of its "
        "preceding tasks failed.",
        "skip_unchanged": "Internal decorator applied to tasks which have already been "
        "executed and have not been changed.",
        "skipif": "Skip a task and all its dependent tasks if a condition is met.",
    }
    config["markers"] = {**config["markers"], **markers}


@hookimpl
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Take a short-cut for skipped tasks during setup with an exception."""
    is_unchanged = has_mark(task, "skip_unchanged") and not has_mark(
        task, "would_be_executed"
    )
    if is_unchanged and not session.config["force"]:
        raise SkippedUnchanged

    ancestor_failed_marks = get_marks(task, "skip_ancestor_failed")
    if ancestor_failed_marks:
        message = "\n".join(
            skip_ancestor_failed(*mark.args, **mark.kwargs)
            for mark in ancestor_failed_marks
        )
        raise SkippedAncestorFailed(message)

    is_skipped = has_mark(task, "skip")
    if is_skipped:
        raise Skipped

    skipif_marks = get_marks(task, "skipif")
    if skipif_marks:
        marker_args = [skipif(*mark.args, **mark.kwargs) for mark in skipif_marks]
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
    return None
