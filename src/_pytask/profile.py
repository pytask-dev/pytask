"""Contains the code to profile the execution."""

from __future__ import annotations

import csv
import enum
import json
import sys
import time
from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

import click
from rich.table import Table

from _pytask.click import ColoredCommand
from _pytask.click import EnumChoice
from _pytask.console import console
from _pytask.console import format_task_name
from _pytask.dag import create_dag
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.outcomes import ExitCode
from _pytask.outcomes import TaskOutcome
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import storage
from _pytask.runtime_store import RuntimeState
from _pytask.session import Session
from _pytask.traceback import Traceback

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from typing import NoReturn

    from _pytask.reports import ExecutionReport


class _ExportFormats(enum.Enum):
    NO = "no"
    JSON = "json"
    CSV = "csv"


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(profile)


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Register the export option."""
    runtime_state = RuntimeState.from_root(config["root"])
    config["pm"].register(ProfilePlugin(runtime_state))
    config["pm"].register(DurationNameSpace(runtime_state))
    config["pm"].register(ExportNameSpace)
    config["pm"].register(FileSizeNameSpace)


@hookimpl(wrapper=True)
def pytask_execute_task(task: PTask) -> Generator[None, None, None]:
    """Attach the duration of the execution to the task."""
    start = time.time()
    result = yield
    end = time.time()
    task.attributes["duration"] = (start, end)
    return result


@dataclass
class ProfilePlugin:
    """Collect and persist runtime profiling data."""

    runtime_state: RuntimeState

    @hookimpl
    def pytask_execute_task_process_report(
        self, session: Session, report: ExecutionReport
    ) -> None:
        """Store runtime of successfully finishing tasks."""
        _ = session
        task = report.task
        duration = task.attributes.get("duration")
        if report.outcome == TaskOutcome.SUCCESS and duration is not None:
            self.runtime_state.update_task(task, *duration)

    @hookimpl
    def pytask_unconfigure(self, session: Session) -> None:
        """Flush runtime information on normal build exits."""
        if session.config.get("command") != "build":
            return
        if session.config.get("dry_run") or session.config.get("explain"):
            return
        self.runtime_state.flush()


@dataclass
class DurationNameSpace:
    """A namespace for adding durations to the profile."""

    def __init__(self, runtime_state: RuntimeState) -> None:
        self.runtime_state = runtime_state

    @hookimpl
    def pytask_profile_add_info_on_task(
        self, session: Session, tasks: list[PTask], profile: dict[str, dict[str, Any]]
    ) -> None:
        """Add the runtime for tasks to the profile."""
        _ = session
        for task in tasks:
            duration = self.runtime_state.get_duration(task)
            if duration is not None:
                profile[task.name]["Duration (in s)"] = round(duration, 2)


@click.command(cls=ColoredCommand)
@click.option(
    "--export",
    type=EnumChoice(_ExportFormats),
    default=_ExportFormats.NO,
    help="Export the profile in the specified format.",
)
def profile(**raw_config: Any) -> NoReturn:
    """Show information about resource consumption."""
    pm = storage.get()
    raw_config["command"] = "profile"

    try:
        config = pm.hook.pytask_configure(pm=pm, raw_config=raw_config)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):  # noqa: BLE001  # pragma: no cover
        session = Session(exit_code=ExitCode.CONFIGURATION_FAILED)
        console.print(Traceback(sys.exc_info()))

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)
            session.dag = create_dag(session=session)

            profile: dict[str, dict[str, Any]] = {
                task.name: {} for task in session.tasks
            }
            session.hook.pytask_profile_add_info_on_task(
                session=session, tasks=session.tasks, profile=profile
            )
            profile = _process_profile(profile)

            _print_profile_table(profile, session.tasks, session.config)

            session.hook.pytask_profile_export_profile(session=session, profile=profile)

            console.rule(style="neutral")

        except CollectionError:  # pragma: no cover
            session.exit_code = ExitCode.COLLECTION_FAILED

        except Exception:  # noqa: BLE001 pragma: no cover
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style="failed")

    session.hook.pytask_unconfigure(session=session)
    sys.exit(session.exit_code)


def _print_profile_table(
    profile: dict[str, dict[str, Any]], tasks: list[PTask], config: dict[str, Any]
) -> None:
    """Print the profile table."""
    name_to_task = {task.name: task for task in tasks}
    info_names = _get_info_names(profile)

    console.print()
    if profile:
        table = Table("Task")
        for name in info_names:
            table.add_column(name, justify="right")

        for task_name, info in profile.items():
            task_id = format_task_name(
                task=name_to_task[task_name],
                editor_url_scheme=config["editor_url_scheme"],
            )
            infos = [str(i) for i in info.values()]
            table.add_row(task_id, *infos)

        console.print(table)
    else:
        console.print("No information is stored on the collected tasks.")


class FileSizeNameSpace:
    """A namespace for adding the total file size of products to a task."""

    @staticmethod
    @hookimpl
    def pytask_profile_add_info_on_task(
        session: Session, tasks: list[PTask], profile: dict[str, dict[str, Any]]
    ) -> None:
        """Add the total file size of all products for a task."""
        for task in tasks:
            successors = list(session.dag.successors(task.signature))
            if successors:
                sum_bytes = 0
                for successor in successors:
                    node = session.dag.nodes[successor]["node"]
                    if isinstance(node, PPathNode):
                        with suppress(FileNotFoundError):
                            sum_bytes += node.path.stat().st_size

                profile[task.name]["Size of Products"] = _to_human_readable_size(
                    sum_bytes
                )


def _to_human_readable_size(bytes_: int, units: list[str] | None = None) -> str:
    """Convert bytes to a human readable size."""
    units = [" bytes", " KB", " MB", " GB", " TB"] if units is None else units
    return (
        str(bytes_) + units[0]
        if bytes_ < 1024 or len(units) == 1  # noqa: PLR2004
        else _to_human_readable_size(bytes_ >> 10, units[1:])
    )


def _process_profile(profile: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Process profile to make it ready for printing and storing."""
    info_names = _get_info_names(profile)
    if info_names:
        complete_profiles = {
            task_name: {
                attr_name: profile[task_name].get(attr_name, "")
                for attr_name in info_names
            }
            for task_name in sorted(profile)
        }
    else:
        complete_profiles = {}
    return complete_profiles


class ExportNameSpace:
    """A namespace for exporting the profile."""

    @staticmethod
    @hookimpl(trylast=True)
    def pytask_profile_export_profile(
        session: Session, profile: dict[str, dict[str, Any]]
    ) -> None:
        """Export profiles."""
        export = session.config["export"]

        if export == _ExportFormats.CSV:
            _export_to_csv(profile, session.config["root"])
        elif export == _ExportFormats.JSON:
            _export_to_json(profile, session.config["root"])
        elif export == _ExportFormats.NO:
            pass
        else:  # pragma: no cover
            msg = f"The export option {export.value!r} cannot be handled."
            raise ValueError(msg)


def _export_to_csv(profile: dict[str, dict[str, Any]], root: Path) -> None:
    """Export profile to csv."""
    info_names = _get_info_names(profile)
    path = root.joinpath("profile.csv")

    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("Task", *info_names))
        for task_name, info in profile.items():
            writer.writerow((task_name, *info.values()))


def _export_to_json(profile: dict[str, dict[str, Any]], root: Path) -> None:
    """Export profile to json."""
    json_ = json.dumps(profile)
    path = root.joinpath("profile.json")
    path.write_text(json_)


def _get_info_names(profile: dict[str, dict[str, Any]]) -> list[str]:
    """Get names of infos of tasks.

    Examples
    --------
    >>> _get_info_names({"t1": {"time": 1}, "t2": {"time": 1, "size": "2GB"}})
    ['size', 'time']
    >>> _get_info_names({})
    []
    >>> _get_info_names({"t1": {}})
    []

    """
    base: set[str] = set()
    info_names: list[str] = sorted(base.union(*(set(val) for val in profile.values())))
    return info_names
