from pathlib import Path

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
    is_verbose = config["verbose"] >= 1
    live_execution = LiveExecution(is_verbose, config["paths"])
    config["pm"].register(live_execution, "live_execution")


def generate_collection_status(n_collected_tasks):
    """Generate the status object to display the progress during collection."""
    return Status(
        f"Collected {n_collected_tasks} tasks.", refresh_per_second=4, spinner="dots"
    )


@attr.s(eq=False)
class LiveExecution:
    """A singleton for a live display of the execution as a table."""

    _is_verbose = attr.ib(type=bool)
    _paths = attr.ib(type=Path)
    _live = Live(renderable=None, console=console, auto_refresh=False)
    _running_tasks = attr.ib(factory=set)
    _reports = attr.ib(factory=list)

    def update_running_tasks(self, new_running_task):
        reduced_task_name = reduce_node_name(new_running_task, self._paths)
        self._running_tasks.add(reduced_task_name)
        self._update_table()

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
        self._update_table()

    def start(self):
        if self._is_verbose:
            self._live.start()

    def stop(self):
        if self._is_verbose:
            self._live.stop()

    def pause(self):
        self._live.transient = True
        self.stop()

    def resume(self):
        self._live.transient = False
        self.start()

    def _generate_table(self):
        if self._running_tasks or self._reports:
            table = Table("Task", "Outcome")
            for report in self._reports:
                table.add_row(
                    report["name"], Text(report["symbol"], style=report["color"])
                )
            for running_task in self._running_tasks:
                table.add_row(running_task, "running")
        else:
            table = None

        return table

    def _update_table(self):
        table = self._generate_table()
        self._live.update(table)
        self._live.refresh()

    @hookimpl(hookwrapper=True)
    def pytask_execute_build(self):
        if self._is_verbose:
            self.start()
            yield
            self.stop()
        else:
            yield

    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_start(self, task):
        if self._is_verbose:
            self.update_running_tasks(task)
            return True

    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_end(self, report):
        if self._is_verbose:
            self.update_reports(report)
            return True
