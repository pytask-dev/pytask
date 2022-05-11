"""This module contains code related to live objects."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Union

import attr
import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import format_task_id
from _pytask.nodes import Task
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.report import CollectionReport
from _pytask.report import ExecutionReport
from _pytask.session import Session
from _pytask.shared import get_first_non_none_value
from rich.live import Live
from rich.status import Status
from rich.style import Style
from rich.table import Table
from rich.text import Text


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend command line interface."""
    additional_parameters = [
        click.Option(
            ["--n-entries-in-table"],
            default=None,
            help="How many entries to display in the table during the execution. "
            "Tasks which are running are always displayed. [dim]\\[default: 15][/]",
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(
    config: dict[str, Any],
    config_from_cli: dict[str, Any],
    config_from_file: dict[str, Any],
) -> None:
    """Parse the configuration."""
    config["n_entries_in_table"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="n_entries_in_table",
        default=15,
        callback=_parse_n_entries_in_table,
    )


def _parse_n_entries_in_table(value: int | str | None) -> int:
    """Parse how many entries should be displayed in the table during the execution."""
    if value in ["none", "None", None, ""]:
        out = None
    elif isinstance(value, int) and value >= 1:
        out = value
    elif isinstance(value, str) and value.isdigit() and int(value) >= 1:
        out = int(value)
    elif value == "all":
        out = 1_000_000
    else:
        raise ValueError(
            "'n_entries_in_table' can either be 'None' or an integer bigger than one."
        )
    return out


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Post-parse the configuration."""
    live_manager = LiveManager()
    config["pm"].register(live_manager, "live_manager")

    if config["verbose"] >= 1:
        live_execution = LiveExecution(
            live_manager=live_manager,
            n_entries_in_table=config["n_entries_in_table"],
            verbose=config["verbose"],
            editor_url_scheme=config["editor_url_scheme"],
            sort_final_table=config["sort_table"],
        )
        config["pm"].register(live_execution, "live_execution")

    live_collection = LiveCollection(live_manager=live_manager)
    config["pm"].register(live_collection, "live_collection")


@hookimpl(hookwrapper=True)
def pytask_execute(session: Session) -> Generator[None, None, None]:
    if session.config["verbose"] >= 1:
        live_execution = session.config["pm"].get_plugin("live_execution")
        if live_execution:
            live_execution.n_tasks = len(session.tasks)

    yield


@attr.s(eq=False)
class LiveManager:
    """A class for live displays during a session.

    This class allows to display live information during a session and handles the
    interaction with the :class:`_pytask.debugging.PytaskPDB`.

    The renderable is not updated automatically for two reasons.

    1. Usually, the duration of tasks is highly heterogeneous and there are probably not
       many tasks which last much less than a second. Therefore, updating the renderable
       automatically by a fixed time interval seems unnecessary.

    2. To update the renderable automatically a thread is started which pushes the
       updates. When a task is run simultaneously and capturing is activated, all
       updates will be captured and added to the stdout of the task instead of printed
       to the terminal.

    """

    _live = Live(renderable=None, console=console, auto_refresh=False)

    def start(self) -> None:
        self._live.start()

    def stop(self, transient: bool | None = None) -> None:
        if transient is not None:
            self._live.transient = transient
        self._live.stop()

    def pause(self) -> None:
        self._live.transient = True
        self.stop()

    def resume(self) -> None:
        if not self._live.renderable:
            return
        self._live.transient = False
        self.start()

    def update(self, *args: Any, **kwargs: Any) -> None:
        self._live.update(*args, **kwargs)
        self._live.refresh()

    @property
    def is_started(self) -> None:
        return self._live.is_started


@attr.s(eq=False, kw_only=True)
class LiveExecution:
    """A class for managing the table displaying task progress during the execution."""

    live_manager = attr.ib(type=LiveManager)
    n_entries_in_table = attr.ib(type=int)
    verbose = attr.ib(type=int)
    editor_url_scheme = attr.ib(type=str)
    sort_final_table = attr.ib(default=False, type=bool)
    n_tasks = attr.ib(default="x", type=Union[int, str])
    _reports = attr.ib(factory=list, type=List[Dict[str, Any]])
    _running_tasks = attr.ib(factory=dict, type=Dict[str, Task])

    @hookimpl(hookwrapper=True)
    def pytask_execute_build(self) -> Generator[None, None, None]:
        """Wrap the execution with the live manager and yield a complete table at the
        end."""
        self.live_manager.start()
        yield
        self.live_manager.stop(transient=True)
        table = self._generate_table(
            reduce_table=False, sort_table=self.sort_final_table, add_caption=False
        )
        if table is not None:
            console.print(table)

    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_start(self, task: Task) -> bool:
        """Mark a new task as running."""
        self.update_running_tasks(task)
        return True

    @hookimpl
    def pytask_execute_task_log_end(self, report: ExecutionReport) -> bool:
        """Mark a task as being finished and update outcome."""
        self.update_reports(report)
        return True

    def _generate_table(
        self, reduce_table: bool, sort_table: bool, add_caption: bool
    ) -> Table | None:
        """Generate the table.

        First, display all completed tasks and, then, all running tasks.

        The number of entries can be limited. All running tasks are always displayed and
        if more entries are requested, the list is filled up with completed tasks.

        """
        n_reports_to_display = self.n_entries_in_table - len(self._running_tasks)

        if self.verbose < 2:
            reports = [
                report
                for report in self._reports
                if report["outcome"]
                not in (
                    TaskOutcome.SKIP,
                    TaskOutcome.SKIP_UNCHANGED,
                    TaskOutcome.SKIP_PREVIOUS_FAILED,
                    TaskOutcome.PERSISTENCE,
                )
            ]
        else:
            reports = self._reports

        if not reduce_table:
            relevant_reports = reports
        elif n_reports_to_display >= 1:
            relevant_reports = reports[-n_reports_to_display:]
        else:
            relevant_reports = []

        if sort_table:
            relevant_reports = sorted(
                relevant_reports, key=lambda report: report["name"]
            )

        if add_caption:
            caption_kwargs = {
                "caption": Text(
                    f"Completed: {len(self._reports)}/{self.n_tasks}",
                    style=Style(dim=True, italic=False),
                ),
                "caption_justify": "right",
                "caption_style": None,
            }
        else:
            caption_kwargs = {}

        table = Table(**caption_kwargs)
        table.add_column("Task", overflow="fold")
        table.add_column("Outcome")
        for report in relevant_reports:
            table.add_row(
                format_task_id(
                    report["task"],
                    editor_url_scheme=self.editor_url_scheme,
                    short_name=True,
                ),
                Text(report["outcome"].symbol, style=report["outcome"].style),
            )
        for task in self._running_tasks.values():
            table.add_row(
                format_task_id(
                    task, editor_url_scheme=self.editor_url_scheme, short_name=True
                ),
                "running",
            )

        # If the table is empty, do not display anything.
        if table.rows == []:
            table = None

        return table

    def _update_table(
        self,
        reduce_table: bool = True,
        sort_table: bool = False,
        add_caption: bool = True,
    ) -> None:
        """Regenerate the table."""
        table = self._generate_table(
            reduce_table=reduce_table, sort_table=sort_table, add_caption=add_caption
        )
        self.live_manager.update(table)

    def update_running_tasks(self, new_running_task: Task) -> None:
        """Add a new running task."""
        self._running_tasks[new_running_task.name] = new_running_task
        self._update_table()

    def update_reports(self, new_report: ExecutionReport) -> None:
        """Update the status of a running task by adding its report."""
        self._running_tasks.pop(new_report.task.name)
        self._reports.append(
            {
                "name": new_report.task.short_name,
                "outcome": new_report.outcome,
                "task": new_report.task,
            }
        )
        self._update_table()


@attr.s(eq=False, kw_only=True)
class LiveCollection:
    """A class for managing the live status during the collection."""

    live_manager = attr.ib(type=LiveManager)
    _n_collected_tasks = attr.ib(default=0, type=int)
    _n_errors = attr.ib(default=0, type=int)

    @hookimpl(hookwrapper=True)
    def pytask_collect(self) -> Generator[None, None, None]:
        """Start the status of the collection."""
        self.live_manager.start()
        yield

    @hookimpl
    def pytask_collect_file_log(self, reports: list[CollectionReport]) -> None:
        """Update the status after a file is collected."""
        self._update_statistics(reports)
        self._update_status()

    @hookimpl(hookwrapper=True)
    def pytask_collect_log(self) -> Generator[None, None, None]:
        """Stop the live display when all tasks have been collected."""
        self.live_manager.stop(transient=True)
        yield

    def _update_statistics(self, reports: list[CollectionReport]) -> None:
        """Update the statistics on collected tasks and errors."""
        if reports is None:
            reports = []
        for report in reports:
            if report.outcome == CollectionOutcome.SUCCESS:
                self._n_collected_tasks += 1
            else:
                self._n_errors += 1

    def _update_status(self) -> None:
        """Update the status."""
        status = self._generate_status()
        self.live_manager.update(status)

    def _generate_status(self) -> Status:
        """Generate the status."""
        msg = f"Collected {self._n_collected_tasks} tasks."
        if self._n_errors > 0:
            msg += f" {self._n_errors} errors."
        status = Status(msg, spinner="dots")
        return status
