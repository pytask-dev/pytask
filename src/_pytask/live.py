from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Set
from typing import Union

import attr
import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import create_url_style_for_task
from _pytask.nodes import MetaTask
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.report import CollectionReport
from _pytask.report import ExecutionReport
from _pytask.shared import get_first_non_none_value
from _pytask.shared import reduce_node_name
from rich.live import Live
from rich.status import Status
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
            "Tasks which are running are always displayed.  [default: 15]",
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(
    config: Dict[str, Any],
    config_from_cli: Dict[str, Any],
    config_from_file: Dict[str, Any],
) -> None:
    config["n_entries_in_table"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="n_entries_in_table",
        default=15,
        callback=_parse_n_entries_in_table,
    )


def _parse_n_entries_in_table(value: Union[int, str, None]) -> int:
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
def pytask_post_parse(config: Dict[str, Any]) -> None:
    live_manager = LiveManager()
    config["pm"].register(live_manager, "live_manager")

    if config["verbose"] >= 1:
        live_execution = LiveExecution(
            live_manager,
            config["paths"],
            config["n_entries_in_table"],
            config["verbose"],
            config["editor_url_scheme"],
        )
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

    _live = Live(renderable=None, console=console, auto_refresh=True)

    def start(self) -> None:
        self._live.start()

    def stop(self, transient: Optional[bool] = None) -> None:
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

    @property
    def is_started(self) -> None:
        return self._live.is_started


@attr.s(eq=False)
class LiveExecution:

    _live_manager = attr.ib(type=LiveManager)
    _paths = attr.ib(type=List[Path])
    _n_entries_in_table = attr.ib(type=int)
    _verbose = attr.ib(type=int)
    _editor_url_scheme = attr.ib(type=str, default="file")
    _running_tasks = attr.ib(factory=set, type=Set[str])
    _reports = attr.ib(factory=list, type=List[Dict[str, Any]])

    @hookimpl(hookwrapper=True)
    def pytask_execute_build(self) -> Generator[None, None, None]:
        self._live_manager.start()
        yield
        self._update_table(reduce_table=False)
        self._live_manager.stop(transient=False)

    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_start(self, task: MetaTask) -> bool:
        self.update_running_tasks(task)
        return True

    @hookimpl
    def pytask_execute_task_log_end(self, report: ExecutionReport) -> bool:
        self.update_reports(report)
        return True

    def _generate_table(self, reduce_table: bool) -> Optional[Table]:
        """Generate the table.

        First, display all completed tasks and, then, all running tasks.

        The number of entries can be limited. All running tasks are always displayed and
        if more entries are requested, the list is filled up with completed tasks.

        """
        if self._running_tasks or self._reports:

            n_reports_to_display = self._n_entries_in_table - len(self._running_tasks)
            if not reduce_table:
                relevant_reports = self._reports
            elif n_reports_to_display >= 1:
                relevant_reports = self._reports[-n_reports_to_display:]
            else:
                relevant_reports = []

            table = Table("Task", "Outcome")
            for report in relevant_reports:
                if (
                    report["outcome"]
                    in (
                        TaskOutcome.SKIP,
                        TaskOutcome.SKIP_UNCHANGED,
                        TaskOutcome.SKIP_PREVIOUS_FAILED,
                        TaskOutcome.PERSISTENCE,
                    )
                    and self._verbose < 2
                ):
                    pass
                else:
                    table.add_row(
                        Text(
                            report["name"],
                            style=create_url_style_for_task(
                                report["task"], self._editor_url_scheme
                            ),
                        ),
                        Text(report["outcome"].symbol, style=report["outcome"].style),
                    )
            for running_task in self._running_tasks:
                table.add_row(running_task, "running")
        else:
            table = None

        return table

    def _update_table(self, reduce_table: bool = True) -> None:
        table = self._generate_table(reduce_table)
        self._live_manager.update(table)

    def update_running_tasks(self, new_running_task: MetaTask) -> None:
        reduced_task_name = reduce_node_name(new_running_task, self._paths)
        self._running_tasks.add(reduced_task_name)
        self._update_table()

    def update_reports(self, new_report: ExecutionReport) -> None:
        reduced_task_name = reduce_node_name(new_report.task, self._paths)
        self._running_tasks.remove(reduced_task_name)
        self._reports.append(
            {
                "name": reduced_task_name,
                "outcome": new_report.outcome,
                "task": new_report.task,
            }
        )
        self._update_table()


@attr.s(eq=False)
class LiveCollection:

    _live_manager = attr.ib(type=LiveManager)
    _n_collected_tasks = attr.ib(default=0, type=int)
    _n_errors = attr.ib(default=0, type=int)

    @hookimpl(hookwrapper=True)
    def pytask_collect(self) -> Generator[None, None, None]:
        self._live_manager.start()
        yield

    @hookimpl
    def pytask_collect_file_log(self, reports: List[CollectionReport]) -> None:
        self._update_statistics(reports)
        self._update_status()

    @hookimpl(hookwrapper=True)
    def pytask_collect_log(self) -> Generator[None, None, None]:
        self._live_manager.update(None)
        self._live_manager.stop(transient=True)
        yield

    def _update_statistics(self, reports: List[CollectionReport]) -> None:
        if reports is None:
            reports = []
        for report in reports:
            if report.outcome == CollectionOutcome.SUCCESS:
                self._n_collected_tasks += 1
            else:
                self._n_errors += 1

    def _update_status(self) -> None:
        status = self._generate_status()
        self._live_manager.update(status)

    def _generate_status(self) -> Status:
        msg = f"Collected {self._n_collected_tasks} tasks."
        if self._n_errors > 0:
            msg += f" {self._n_errors} errors."
        status = Status(msg, spinner="dots")
        return status
