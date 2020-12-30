"""This module contains everything related to skipping tasks."""
import click
from _pytask.config import hookimpl
from _pytask.dag import descending_tasks
from _pytask.enums import ColorCode
from _pytask.mark import get_specific_markers_from_task
from _pytask.mark import Mark
from _pytask.outcomes import Skipped
from _pytask.outcomes import SkippedAncestorFailed
from _pytask.outcomes import SkippedUnchanged
from _pytask.traceback import remove_traceback_from_exc_info


def skip_ancestor_failed(reason: str = "No reason provided.") -> str:
    """Function to parse information in ``@pytask.mark.skip_ancestor_failed``."""
    return reason


@hookimpl
def pytask_parse_config(config):
    markers = {
        "skip": "Skip a task and all its subsequent tasks as well.",
        "skip_ancestor_failed": "Internal decorator applied to tasks whose ancestor "
        "failed.",
        "skip_unchanged": "Internal decorator applied to tasks which have already been "
        "executed and have not been changed.",
    }
    config["markers"] = {**config["markers"], **markers}


@hookimpl
def pytask_execute_task_setup(task):
    """Take a short-cut for skipped tasks during setup with an exception."""
    markers = get_specific_markers_from_task(task, "skip_unchanged")
    if markers:
        raise SkippedUnchanged

    markers = get_specific_markers_from_task(task, "skip_ancestor_failed")
    if markers:
        message = "\n".join(
            [skip_ancestor_failed(*marker.args, **marker.kwargs) for marker in markers]
        )
        raise SkippedAncestorFailed(message)

    markers = get_specific_markers_from_task(task, "skip")
    if markers:
        raise Skipped


@hookimpl
def pytask_execute_task_process_report(session, report):
    """Process the execution reports for skipped tasks.

    This functions allows to turn skipped tasks to successful tasks.

    """
    task = report.task

    if report.exc_info:
        if isinstance(report.exc_info[1], SkippedUnchanged):
            report.success = True

        elif isinstance(report.exc_info[1], Skipped):
            report.success = True
            for descending_task_name in descending_tasks(task.name, session.dag):
                descending_task = session.dag.nodes[descending_task_name]["task"]
                descending_task.markers.append(
                    Mark(
                        "skip",
                        (),
                        {"reason": f"Previous task '{task.name}' was skipped."},
                    )
                )

        elif isinstance(report.exc_info[1], SkippedAncestorFailed):
            report.success = False
            report.exc_info = remove_traceback_from_exc_info(report.exc_info)

    if report.exc_info and isinstance(
        report.exc_info[1], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
    ):
        return True


@hookimpl
def pytask_execute_task_log_end(report):
    """Log the status of a skipped task."""
    if report.success:
        if report.exc_info:
            if isinstance(report.exc_info[1], Skipped):
                click.secho("s", fg=ColorCode.SKIPPED, nl=False)
            elif isinstance(report.exc_info[1], SkippedUnchanged):
                click.secho("s", fg=ColorCode.SUCCESS, nl=False)
    else:
        if report.exc_info and isinstance(report.exc_info[1], SkippedAncestorFailed):
            click.secho("s", fg=ColorCode.FAILED, nl=False)

    if report.exc_info and isinstance(
        report.exc_info[1], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
    ):
        # Return non-None value so that the task is not logged again.
        return True
