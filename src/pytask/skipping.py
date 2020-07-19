import click
import pytask
from pytask.dag import descending_tasks
from pytask.mark import get_markers_from_task
from pytask.mark import Mark
from pytask.outcomes import Skipped
from pytask.outcomes import SkippedAncestorFailed
from pytask.outcomes import SkippedUnchanged


@pytask.hookimpl
def pytask_execute_task_setup(task):
    markers = get_markers_from_task(task, "skip_unchanged")
    if markers:
        raise SkippedUnchanged

    markers = get_markers_from_task(task, "skip_ancestor_failed")
    if markers:
        message = "\n".join([marker.kwargs["reason"] for marker in markers])
        raise SkippedAncestorFailed(message)

    markers = get_markers_from_task(task, "skip")
    if markers:
        raise Skipped


@pytask.hookimpl
def pytask_execute_task_process_report(session, report):
    task = report.task

    if report.exc_info and isinstance(report.exc_info[1], SkippedUnchanged):
        report.success = True

    elif report.exc_info and isinstance(report.exc_info[1], Skipped):
        report.success = True
        for descending_task_name in descending_tasks(report.task.name, session.dag):
            descending_task = session.dag.nodes[descending_task_name]["task"]
            descending_task.markers.append(
                Mark(
                    "skip", (), {"reason": f"Previous task '{task.name}' was skipped."},
                )
            )

    elif report.exc_info and isinstance(report.exc_info[1], SkippedAncestorFailed):
        report.success = False
        report.exc_info = _remove_traceback_from_exc_info(report.exc_info)

    if report.exc_info and isinstance(
        report.exc_info[1], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
    ):
        return True


@pytask.hookimpl
def pytask_execute_task_log_end(report):
    if report.success:
        if report.exc_info and isinstance(report.exc_info[1], Skipped):
            click.secho("s", fg="yellow", nl=False)
        elif report.exc_info and isinstance(report.exc_info[1], SkippedUnchanged):
            click.secho("s", fg="green", nl=False)
    else:
        if report.exc_info and isinstance(report.exc_info[1], SkippedAncestorFailed):
            click.secho("s", fg="red", nl=False)

    if report.exc_info and isinstance(
        report.exc_info[1], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
    ):
        # Return non-None value so that the task is not logged again.
        return True


def _remove_traceback_from_exc_info(exc_info):
    return (*exc_info[:2], None)
