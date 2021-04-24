import time

from _pytask.config import hookimpl
from _pytask.database import db
from pony import orm


class Runtime(db.Entity):
    """Record of runtimes of tasks."""

    task = orm.PrimaryKey(str)
    date = orm.Required(float)
    duration = orm.Required(float)


@hookimpl(hookwrapper=True)
def pytask_execute_task(task):
    """Attach the duration of the execution to the task."""
    start = time.time()
    yield
    end = time.time()
    task.attributes["duration"] = (start, end)


@hookimpl
def pytask_execute_task_process_report(report):
    task = report.task
    if report.success and task.attributes.get("duration") is not None:
        _create_or_update_runtime(task.name, *task.attributes["duration"])


@orm.db_session
def _create_or_update_runtime(task_name, start, end):
    """Create or update a runtime entry."""
    try:
        runtime = Runtime[task_name]
    except orm.ObjectNotFound:
        Runtime(task=task_name, date=start, duration=end - start)
    else:
        for attr, val in [("date", start), ("duration", end - start)]:
            setattr(runtime, attr, val)
