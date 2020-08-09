import click
from _pytask.config import hookimpl
from _pytask.dag import descending_tasks
from _pytask.enums import ColorCode
from _pytask.mark import get_specific_markers_from_task
from _pytask.mark import Mark
from _pytask.outcomes import Skipped
from _pytask.outcomes import SkippedAncestorFailed
from _pytask.outcomes import SkippedUnchanged
from _pytask.shared import remove_traceback_from_exc_info


@hookimpl
def pytask_parse_config(config):
    markers = {
        "skip": "skip: Skip task and all its succeeding tasks automatically as well.",
        "skip_ancestor_failed": "skip_ancestor_failed: Internal decorator applied to "
        "tasks whose ancestor failed.",
        "skip_unchanged": "skip_unchanged: Internal decorator applied to tasks which "
        "have already been executed and have not been changed.",
    }
    config["markers"] = {**config["markers"], **markers}


@hookimpl
def pytask_execute_task_setup(task):
    markers = get_specific_markers_from_task(task, "skip_unchanged")
    if markers:
        raise SkippedUnchanged

    markers = get_specific_markers_from_task(task, "skip_ancestor_failed")
    if markers:
        message = "\n".join([marker.kwargs["reason"] for marker in markers])
        raise SkippedAncestorFailed(message)

    markers = get_specific_markers_from_task(task, "skip")
    if markers:
        raise Skipped


@hookimpl
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
        report.exc_info = remove_traceback_from_exc_info(report.exc_info)

    if report.exc_info and isinstance(
        report.exc_info[1], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
    ):
        return True


@hookimpl
def pytask_execute_task_log_end(report):
    if report.success:
        if report.exc_info and isinstance(report.exc_info[1], Skipped):
            click.secho("s", fg=ColorCode.SKIPPED.value, nl=False)
        elif report.exc_info and isinstance(report.exc_info[1], SkippedUnchanged):
            click.secho("s", fg=ColorCode.SUCCESS.value, nl=False)
    else:
        if report.exc_info and isinstance(report.exc_info[1], SkippedAncestorFailed):
            click.secho("s", fg=ColorCode.FAILED.value, nl=False)

    if report.exc_info and isinstance(
        report.exc_info[1], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
    ):
        # Return non-None value so that the task is not logged again.
        return True
