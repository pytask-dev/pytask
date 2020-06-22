import click
import pytask
from pytask.dag import task_and_descending_tasks
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
def pytask_execute_task_process_result(session, result):
    if isinstance(result["value"], SkippedUnchanged):
        result["success"] = True

    elif isinstance(result["value"], Skipped):
        result["success"] = True
        for descending_task_name in task_and_descending_tasks(
            result["task"].name, session.dag
        ):
            descending_task = session.dag.nodes[descending_task_name]["task"]
            descending_task.markers.append(Mark("skip", (), {},))

    elif isinstance(result["value"], SkippedAncestorFailed):
        result["success"] = False
        result["traceback"] = None

    if isinstance(result["value"], (Skipped, SkippedUnchanged, SkippedAncestorFailed)):
        return True


@pytask.hookimpl
def pytask_execute_task_log_end(result):
    value = result["value"]
    if result["success"]:
        if isinstance(value, Skipped):
            click.secho("s", fg="yellow", nl=False)
        elif isinstance(value, SkippedUnchanged):
            click.secho("s", fg="green", nl=False)
    else:
        if isinstance(value, SkippedAncestorFailed):
            click.secho("s", fg="red", nl=False)

    if isinstance(value, (Skipped, SkippedUnchanged, SkippedAncestorFailed)):
        # Return non-None value so that the task is not logged again.
        return True
