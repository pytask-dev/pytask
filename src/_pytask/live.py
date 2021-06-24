import attr
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.shared import reduce_node_name
from rich.live import Live
from rich.status import Status
from rich.table import Table
from rich.text import Text


@hookimpl
def pytask_post_parse(config):
    if config["verbose"] >= 1:
        config["pm"].register(ExecutionLiveNamespace)
    LiveExecution._paths = config["paths"]


def generate_collection_status(n_collected_tasks):
    """Generate the status object to display the progress during collection."""
    return Status(
        f"Collected {n_collected_tasks} tasks.", refresh_per_second=4, spinner="dots"
    )


class ExecutionLiveNamespace:
    """The namespace for a live display of the progress of the execution."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_build():
        with live_execution:
            yield

    @staticmethod
    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_start(task):
        live_execution.update_running_tasks(task)
        return True

    @staticmethod
    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_end(report):
        live_execution.update_reports(report)
        return True


@attr.s
class LiveExecution:
    """A singleton for a live display of the execution as a table."""

    _live = Live(renderable=None, console=console, auto_refresh=False)
    _running_tasks = set()
    _reports = []
    _paths = None

    def __enter__(self):
        return self._live.__enter__()

    def __exit__(self, exc_type, exc_value, exc_tb):
        return self._live.__exit__(exc_type, exc_value, exc_tb)

    def update_running_tasks(self, new_running_task):
        reduced_task_name = reduce_node_name(new_running_task, self._paths)
        self._running_tasks.add(reduced_task_name)
        self.update_table()

    def update_reports(self, new_report):
        reduced_task_name = reduce_node_name(new_report.task, self._paths)
        self._running_tasks.remove(reduced_task_name)
        self._reports.append(
            {
                "name": reduced_task_name,
                "symbol": new_report.symbol,
                "color": new_report.color,
            }
        )
        self.update_table()

    def update_table(self):
        table = Table("Task", "Outcome")
        for report in self._reports:
            table.add_row(report["name"], Text(report["symbol"], style=report["color"]))
        for running_task in self._running_tasks:
            table.add_row(running_task, "running")
        self._live.update(table)
        self._live.refresh()


live_execution = LiveExecution()
