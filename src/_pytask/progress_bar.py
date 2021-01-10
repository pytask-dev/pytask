import time
from concurrent.futures import ThreadPoolExecutor

from _pytask.config import hookimpl
from _pytask.database import db
from pony import orm
from tqdm import tqdm


class _Countdown(tqdm):
    """Provides `update_to(n)` which uses `tqdm.update(delta_n)`."""

    _BAR_FORMAT_TEMPLATE = "{desc}: {percentage:3.0f}%|{bar}{elapsed}/"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bar_format = self._BAR_FORMAT_TEMPLATE + tqdm.format_interval(self.total)

    def update_to(self, n=1):
        """Customly update."""
        if self.last_print_n < self.total:
            self.update()
        else:
            self.n -= n
            self.last_print_n -= n
            self.update()


def timed_future_progress_bar(future, expected_time, increments=10):
    """Display progress bar for expected_time seconds.

    Complete early if future completes. Wait for future if it doesn't complete in
    expected_time.

    """
    interval = expected_time / increments
    with tqdm(total=increments) as pbar:
        for i in range(increments - 1):
            if future.done():
                # finish the progress bar
                # not sure if there's a cleaner way to do this?
                pbar.update(increments - i)
                return
            else:
                time.sleep(interval)
                pbar.update()
        # if the future still hasn't completed, wait for it.
        future.result()
        pbar.update()


class Runtime(db.Entity):
    """Record of task runtimes."""

    task = orm.PrimaryKey(str)
    date = orm.Required(float)
    duration = orm.Required(float)


@hookimpl
def pytask_execute_task(task):
    """Attach the duration of the execution to the task."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        start = time.time()
        executor.submit(task.execute)
    end = time.time()
    task.duration = (start, end)


@hookimpl
def pytask_execute_task_process_report(report):
    task = report.task
    if report.success and task.duration:
        _create_or_update_runtime(task.name, *task.duration)


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
