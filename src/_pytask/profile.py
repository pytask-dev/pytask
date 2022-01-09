"""This module contains the code to profile the execution."""
import csv
import json
import sys
import time
from pathlib import Path
from types import TracebackType
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING

import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import format_task_id
from _pytask.database import db
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.nodes import FilePathNode
from _pytask.nodes import MetaTask
from _pytask.outcomes import ExitCode
from _pytask.outcomes import TaskOutcome
from _pytask.pluginmanager import get_plugin_manager
from _pytask.report import ExecutionReport
from _pytask.session import Session
from _pytask.shared import get_first_non_none_value
from _pytask.traceback import render_exc_info
from pony import orm
from rich.table import Table


if TYPE_CHECKING:
    from typing import NoReturn


class Runtime(db.Entity):  # type: ignore
    """Record of runtimes of tasks."""

    task = orm.PrimaryKey(str)
    date = orm.Required(float)
    duration = orm.Required(float)


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(profile)


@hookimpl
def pytask_parse_config(
    config: Dict[str, Any], config_from_cli: Dict[str, Any]
) -> None:
    """Parse the configuration."""
    config["export"] = get_first_non_none_value(
        config_from_cli, key="export", default=None
    )


@hookimpl
def pytask_post_parse(config: Dict[str, Any]) -> None:
    """Register the export option."""
    config["pm"].register(ExportNameSpace)
    config["pm"].register(DurationNameSpace)
    config["pm"].register(FileSizeNameSpace)


@hookimpl(hookwrapper=True)
def pytask_execute_task(task: MetaTask) -> Generator[None, None, None]:
    """Attach the duration of the execution to the task."""
    start = time.time()
    yield
    end = time.time()
    task.attributes["duration"] = (start, end)


@hookimpl
def pytask_execute_task_process_report(report: ExecutionReport) -> None:
    """Store runtime of successfully finishing tasks in database."""
    task = report.task
    duration = task.attributes.get("duration")
    if report.outcome == TaskOutcome.SUCCESS and duration is not None:
        _create_or_update_runtime(task.name, *duration)


@orm.db_session
def _create_or_update_runtime(task_name: str, start: float, end: float) -> None:
    """Create or update a runtime entry."""
    try:
        runtime = Runtime[task_name]  # type: ignore
    except orm.ObjectNotFound:
        Runtime(task=task_name, date=start, duration=end - start)
    else:
        for attr, val in [("date", start), ("duration", end - start)]:
            setattr(runtime, attr, val)


@click.command()
@click.option(
    "--export",
    type=str,
    default=None,
    help="Export the profile in the specified format.",
)
def profile(**config_from_cli: Any) -> "NoReturn":
    """Show profile information on collected tasks."""
    config_from_cli["command"] = "profile"

    try:
        # Duplication of the same mechanism in :func:`pytask.main.main`.
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)
        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED
        exc_info: Tuple[
            Type[BaseException], BaseException, Optional[TracebackType]
        ] = sys.exc_info()
        console.print(render_exc_info(*exc_info, show_locals=config["show_locals"]))

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)
            session.hook.pytask_resolve_dependencies(session=session)

            profile: Dict[str, Dict[str, Any]] = {
                task.name: {} for task in session.tasks
            }
            session.hook.pytask_profile_add_info_on_task(
                session=session, tasks=session.tasks, profile=profile
            )
            profile = _process_profile(profile)

            _print_profile_table(profile, session.tasks, session.config)

            session.hook.pytask_profile_export_profile(session=session, profile=profile)

            console.rule(style="neutral")

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except Exception:
            session.exit_code = ExitCode.FAILED
            console.print_exception()
            console.rule(style="failed")

    sys.exit(session.exit_code)


def _print_profile_table(
    profile: Dict[str, Dict[str, Any]], tasks: List[MetaTask], config: Dict[str, Any]
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
            task_id = format_task_id(
                task=name_to_task[task_name],
                editor_url_scheme=config["editor_url_scheme"],
                short_name=True,
            )
            infos = [str(i) for i in info.values()]
            table.add_row(task_id, *infos)

        console.print(table)
    else:
        console.print("No information is stored on the collected tasks.")


class DurationNameSpace:
    @staticmethod
    @hookimpl
    def pytask_profile_add_info_on_task(
        tasks: List[MetaTask], profile: Dict[str, Dict[str, Any]]
    ) -> None:
        runtimes = _collect_runtimes([task.name for task in tasks])
        for name, duration in runtimes.items():
            profile[name]["Duration (in s)"] = round(duration, 2)


@orm.db_session
def _collect_runtimes(task_names: List[str]) -> Dict[str, float]:
    """Collect runtimes."""
    runtimes = [Runtime.get(task=task_name) for task_name in task_names]
    runtimes = [r for r in runtimes if r is not None]
    return {r.task: r.duration for r in runtimes}


class FileSizeNameSpace:
    @staticmethod
    @hookimpl
    def pytask_profile_add_info_on_task(
        session: Session, tasks: List[MetaTask], profile: Dict[str, Dict[str, Any]]
    ) -> None:
        for task in tasks:
            successors = list(session.dag.successors(task.name))
            if successors:
                sum_bytes = 0
                for successor in successors:
                    node = session.dag.nodes[successor]["node"]
                    if isinstance(node, FilePathNode):
                        try:
                            sum_bytes += node.path.stat().st_size
                        except FileNotFoundError:
                            pass

                profile[task.name]["Size of Products"] = _to_human_readable_size(
                    sum_bytes
                )


def _to_human_readable_size(bytes_: int, units: Optional[List[str]] = None) -> str:
    """Convert bytes to a human readable size."""
    units = [" bytes", "KB", "MB", "GB", "TB"] if units is None else units
    return (
        str(bytes_) + units[0]
        if bytes_ < 1024
        else _to_human_readable_size(bytes_ >> 10, units[1:])
    )


def _process_profile(profile: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
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
    @staticmethod
    @hookimpl(trylast=True)
    def pytask_profile_export_profile(
        session: Session, profile: Dict[str, Dict[str, Any]]
    ) -> None:
        extension = session.config["export"]

        if extension == "csv":
            _export_to_csv(profile)
        elif extension == "json":
            _export_to_json(profile)
        elif extension is None:
            pass
        else:
            raise ValueError(f"The export option {extension!r} cannot be handled.")


def _export_to_csv(profile: Dict[str, Dict[str, Any]]) -> None:
    """Export profile to csv."""
    info_names = _get_info_names(profile)
    path = Path.cwd().joinpath("profile.csv")

    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("Task", *info_names))
        for task_name, info in profile.items():
            writer.writerow((task_name, *info.values()))


def _export_to_json(profile: Dict[str, Dict[str, Any]]) -> None:
    """Export profile to json."""
    json_ = json.dumps(profile)
    path = Path.cwd().joinpath("profile.json")
    path.write_text(json_)


def _get_info_names(profile: Dict[str, Dict[str, Any]]) -> List[str]:
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
    base: Set[str] = set()
    info_names: List[str] = sorted(base.union(*(set(val) for val in profile.values())))
    return info_names
