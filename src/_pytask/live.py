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
    live_manager = LiveManager()
    config["pm"].register(live_manager, "live_manager")

    if config["verbose"] >= 0:
        live_execution = LiveExecution(live_manager, config["paths"])
        config["pm"].register(live_execution)

    live_collection = LiveCollection(live_manager)
    config["pm"].register(live_collection)


@attr.s(eq=False)
class LiveManager:
    """A class for live displays during a session.

    This class allows to display live information during a session and handles the
    interaction with the :class:`_pytask.debugging.PytaskPDB` and
    :class:`_pytask.capture.CaptureManager`.

    """

    _live = Live(renderable=None, console=console, auto_refresh=False)

    def start(self):
        self._live.start()

    def stop(self, transient=None):
        if transient is not None:
            self._live.transient = transient
        self._live.stop()

    def pause(self):
        self._live.transient = True
        self.stop()

    def resume(self):
        if not self._live.renderable:
            return
        self._live.transient = False
        self.start()

    def update(self, *args, **kwargs):
        self._live.update(*args, **kwargs)

    def refresh(self):
        self._live.refresh()

    @property
    def is_started(self):
        return self._live.is_started


@attr.s(eq=False)
class LiveExecution:

    _live_manager = attr.ib(type=LiveManager)
    _paths = attr.ib(type=Path)
    _running_tasks = attr.ib(factory=set)
    _reports = attr.ib(factory=list)

    @hookimpl(hookwrapper=True)
    def pytask_execute_build(self):
        self._live_manager.start()
        yield
        self._live_manager.stop(transient=False)

    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_start(self, task):
        self.update_running_tasks(task)
        return True

    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_end(self, report):
        self.update_reports(report)
        return True

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
        self._live_manager.update(table)
        self._live_manager.refresh()

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


@attr.s(eq=False)
class LiveCollection:

    _live_manager = attr.ib(type=LiveManager)
    _n_collected_tasks = attr.ib(default=0, type=int)
    _n_errors = attr.ib(default=0, type=int)

    @hookimpl(hookwrapper=True)
    def pytask_collect(self):
        self._live_manager.start()
        yield

    @hookimpl
    def pytask_collect_file_log(self, reports):
        self._update_statistics(reports)
        self._update_status()

    @hookimpl(hookwrapper=True)
    def pytask_collect_log(self):
        self._live_manager.update(None)
        self._live_manager.stop(transient=True)
        yield

    def _update_statistics(self, reports):
        if reports is None:
            reports = []
        for report in reports:
            if report.successful:
                self._n_collected_tasks += 1
            else:
                self._n_errors += 1

    def _update_status(self):
        status = self._generate_status()
        self._live_manager.update(status)
        self._live_manager.refresh()

    def _generate_status(self):
        msg = f"Collected {self._n_collected_tasks} tasks."
        if self._n_errors > 0:
            msg += f" {self._n_errors} errors."
        status = Status(msg, spinner="dots")
        return status
