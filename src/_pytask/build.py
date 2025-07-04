"""Implement the build command."""

from __future__ import annotations

import json
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Literal

import click

from _pytask.capture_utils import CaptureMethod
from _pytask.capture_utils import ShowCapture
from _pytask.click import ColoredCommand
from _pytask.config_utils import find_project_root_and_config
from _pytask.config_utils import read_config
from _pytask.console import console
from _pytask.dag import create_dag
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.outcomes import ExitCode
from _pytask.path import HashPathCache
from _pytask.pluginmanager import get_plugin_manager
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import storage
from _pytask.session import Session
from _pytask.shared import parse_paths
from _pytask.shared import to_list
from _pytask.traceback import Traceback

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import NoReturn

    from _pytask.node_protocols import PTask


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(build_command)


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Fill cache of file hashes with stored hashes."""
    with suppress(Exception):
        path = config["root"] / ".pytask" / "file_hashes.json"
        cache = json.loads(path.read_text())

        for key, value in cache.items():
            HashPathCache.add(key, value)


@hookimpl
def pytask_unconfigure(session: Session) -> None:
    """Save calculated file hashes to file."""
    path = session.config["root"] / ".pytask" / "file_hashes.json"
    path.write_text(json.dumps(HashPathCache._cache))


def build(  # noqa: C901, PLR0912, PLR0913
    *,
    capture: Literal["fd", "no", "sys", "tee-sys"] | CaptureMethod = CaptureMethod.FD,
    check_casing_of_paths: bool = True,
    config: Path | None = None,
    database_url: str = "",
    debug_pytask: bool = False,
    disable_warnings: bool = False,
    dry_run: bool = False,
    editor_url_scheme: Literal["no_link", "file", "vscode", "pycharm"]  # noqa: PYI051
    | str = "file",
    expression: str = "",
    force: bool = False,
    ignore: Iterable[str] = (),
    marker_expression: str = "",
    max_failures: float = float("inf"),
    n_entries_in_table: int = 15,
    paths: Path | Iterable[Path] = (),
    pdb: bool = False,
    pdb_cls: str = "",
    s: bool = False,
    show_capture: Literal["no", "stdout", "stderr", "all"]
    | ShowCapture = ShowCapture.ALL,
    show_errors_immediately: bool = False,
    show_locals: bool = False,
    show_traceback: bool = True,
    sort_table: bool = True,
    stop_after_first_failure: bool = False,
    strict_markers: bool = False,
    tasks: Callable[..., Any] | PTask | Iterable[Callable[..., Any] | PTask] = (),
    task_files: Iterable[str] = ("task_*.py",),
    trace: bool = False,
    verbose: int = 1,
    **kwargs: Any,
) -> Session:
    """Run pytask.

    This is the main command to run pytask which usually receives kwargs from the
    command line interface. It can also be used to run pytask interactively. Pass
    configuration in a dictionary.

    Parameters
    ----------
    capture
        The capture method for stdout and stderr.
    check_casing_of_paths
        Whether errors should be raised when file names have different casings.
    config
        A path to the configuration file.
    database_url
        An URL to the database that tracks the status of tasks.
    debug_pytask
        Whether debug information should be shown.
    disable_warnings
        Whether warnings should be disabled and not displayed.
    dry_run
        Whether a dry-run should be performed that shows which tasks need to be rerun.
    editor_url_scheme
        An url scheme that allows to click on task names, node names and filenames and
        jump right into you preferred editor to the right line.
    expression
        Same as ``-k`` on the command line. Select tasks via expressions on task ids.
    force
        Run tasks even though they would be skipped since nothing has changed.
    ignore
        A pattern to ignore files or directories. Refer to ``pathlib.Path.match`` for
        more info.
    marker_expression
        Same as ``-m`` on the command line. Select tasks via marker expressions.
    max_failures
        Stop after some failures.
    n_entries_in_table
        How many entries to display in the table during the execution. Tasks which are
        running are always displayed.
    paths
        A path or collection of paths where pytask looks for the configuration and
        tasks.
    pdb
        Start the interactive debugger on errors.
    pdb_cls
        Start a custom debugger on errors. For example:
        ``--pdbcls=IPython.terminal.debugger:TerminalPdb``
    s
        Shortcut for ``capture="no"``.
    show_capture
        Choose which captured output should be shown for failed tasks.
    show_errors_immediately
        Show errors with tracebacks as soon as the task fails.
    show_locals
        Show local variables in tracebacks.
    show_traceback
        Choose whether tracebacks should be displayed or not.
    sort_table
        Sort the table of tasks at the end of the execution.
    stop_after_first_failure
        Stop after the first failure.
    strict_markers
        Raise errors for unknown markers.
    tasks
        A task or a collection of tasks which can be callables or instances following
        {class}`~pytask.PTask`.
    task_files
        A pattern to describe modules that contain tasks.
    trace
        Enter debugger in the beginning of each task.
    verbose
        Make pytask verbose (>= 0) or quiet (= 0).

    Returns
    -------
    session : pytask.Session
        The session captures all the information of the current run.

    """
    try:
        raw_config = {
            "capture": capture,
            "check_casing_of_paths": check_casing_of_paths,
            "config": config,
            "database_url": database_url,
            "debug_pytask": debug_pytask,
            "disable_warnings": disable_warnings,
            "dry_run": dry_run,
            "editor_url_scheme": editor_url_scheme,
            "expression": expression,
            "force": force,
            "ignore": ignore,
            "marker_expression": marker_expression,
            "max_failures": max_failures,
            "n_entries_in_table": n_entries_in_table,
            "paths": paths,
            "pdb": pdb,
            "pdb_cls": pdb_cls,
            "s": s,
            "show_capture": show_capture,
            "show_errors_immediately": show_errors_immediately,
            "show_locals": show_locals,
            "show_traceback": show_traceback,
            "sort_table": sort_table,
            "stop_after_first_failure": stop_after_first_failure,
            "strict_markers": strict_markers,
            "tasks": tasks,
            "task_files": task_files,
            "trace": trace,
            "verbose": verbose,
        } | kwargs

        if "command" not in raw_config:
            pm = get_plugin_manager()
            storage.store(pm)
        else:
            pm = storage.get()

        # If someone called the programmatic interface, we need to do some parsing.
        if "command" not in raw_config:
            raw_config["command"] = "build"
            # Add defaults from cli.
            from _pytask.cli import DEFAULTS_FROM_CLI  # noqa: PLC0415

            raw_config = {**DEFAULTS_FROM_CLI, **raw_config}

            raw_config["paths"] = parse_paths(raw_config["paths"])

            if raw_config["config"] is not None:
                raw_config["config"] = Path(raw_config["config"]).resolve()
                raw_config["root"] = raw_config["config"].parent
            else:
                (
                    raw_config["root"],
                    raw_config["config"],
                ) = find_project_root_and_config(raw_config["paths"])

            if raw_config["config"] is not None:
                config_from_file = read_config(raw_config["config"])

                if "paths" in config_from_file:
                    paths = config_from_file["paths"]
                    paths = [
                        raw_config["config"].parent.joinpath(path).resolve()
                        for path in to_list(paths)
                    ]
                    config_from_file["paths"] = paths

                raw_config = {**raw_config, **config_from_file}

        config_ = pm.hook.pytask_configure(pm=pm, raw_config=raw_config)

        session = Session.from_config(config_)

    except (ConfigurationError, Exception):
        console.print(Traceback(sys.exc_info()))
        session = Session(exit_code=ExitCode.CONFIGURATION_FAILED)

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)
            session.dag = create_dag(session=session)
            session.hook.pytask_execute(session=session)

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:
            session.exit_code = ExitCode.DAG_FAILED

        except ExecutionError:
            session.exit_code = ExitCode.FAILED

        except Exception:  # noqa: BLE001
            console.print(Traceback(sys.exc_info(), show_locals=True))
            session.exit_code = ExitCode.FAILED

        session.hook.pytask_unconfigure(session=session)
    return session


@click.command(cls=ColoredCommand, name="build")
@click.option(
    "--debug-pytask",
    is_flag=True,
    default=False,
    help="Trace all function calls in the plugin framework.",
)
@click.option(
    "-x",
    "--stop-after-first-failure",
    is_flag=True,
    default=False,
    help="Stop after the first failure.",
)
@click.option(
    "--max-failures",
    type=click.FloatRange(min=1),
    default=float("inf"),
    help="Stop after some failures.",
)
@click.option(
    "--show-errors-immediately",
    is_flag=True,
    default=False,
    help="Show errors with tracebacks as soon as the task fails.",
)
@click.option(
    "--show-traceback/--show-no-traceback",
    type=bool,
    default=True,
    help="Choose whether tracebacks should be displayed or not.",
)
@click.option(
    "--dry-run", type=bool, is_flag=True, default=False, help="Perform a dry-run."
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Execute a task even if it succeeded successfully before.",
)
def build_command(**raw_config: Any) -> NoReturn:
    """Collect tasks, execute them and report the results."""
    raw_config["command"] = "build"
    session = build(**raw_config)
    sys.exit(session.exit_code)
