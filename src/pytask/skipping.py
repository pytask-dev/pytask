import click
import pytask
from pytask.mark import get_markers_from_task
from pytask.outcomes import Skipped
from pytask.outcomes import SkippedAncestorFailed
from pytask.outcomes import SkippedUnchanged


@pytask.hookimpl(tryfirst=True)
def pytask_execute_task_setup(task):
    markers = get_markers_from_task(task, "skip_unchanged")
    if markers:
        raise SkippedUnchanged

    markers = get_markers_from_task(task, "skip_ancestor_failed")
    if markers:
        raise SkippedAncestorFailed

    markers = get_markers_from_task(task, "skip")
    if markers:
        raise Skipped


@pytask.hookimpl(tryfirst=True)
def pytask_execute_task_log_end(result):
    if not result["success"]:
        if isinstance(result["value"], Skipped):
            click.secho("s", fg="yellow", nl=False)
        elif isinstance(result["value"], SkippedUnchanged):
            click.secho("s", fg="green", nl=False)
            # `success = True` prevents error from being printed.
            result["success"] = True
        elif isinstance(result["value"], SkippedAncestorFailed):
            click.secho("s", fg="red", nl=False)

        if isinstance(
            result["value"], (Skipped, SkippedUnchanged, SkippedAncestorFailed)
        ):
            # Return non-None value so that the task is not logged again.
            return True
