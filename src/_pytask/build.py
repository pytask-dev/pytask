"""Implement the build command."""
from __future__ import annotations

import sys
from typing import Any
from typing import TYPE_CHECKING

import click
from _pytask.click import ColoredCommand
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.outcomes import ExitCode
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from rich.traceback import Traceback


if TYPE_CHECKING:
    from typing import NoReturn


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface."""
    cli.add_command(build)


def main(config_from_cli: dict[str, Any]) -> Session:
    """Run pytask.

    This is the main command to run pytask which usually receives kwargs from the
    command line interface. It can also be used to run pytask interactively. Pass
    configuration in a dictionary.

    Parameters
    ----------
    config_from_cli : dict[str, Any]
        A dictionary with options passed to pytask. In general, this dictionary holds
        the information passed via the command line interface.

    Returns
    -------
    session : _pytask.session.Session
        The session captures all the information of the current run.

    """
    try:
        pm = get_plugin_manager()
        from _pytask import cli

        pm.register(cli)
        pm.hook.pytask_add_hooks(pm=pm)

        config = pm.hook.pytask_configure(pm=pm, config_from_cli=config_from_cli)

        session = Session.from_config(config)

    except (ConfigurationError, Exception):
        exc_info = sys.exc_info()
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        traceback = Traceback.from_exception(*exc_info)
        console.print(traceback)
        session = Session({}, None)
        session.exit_code = ExitCode.CONFIGURATION_FAILED

    else:
        try:
            session.hook.pytask_log_session_header(session=session)
            session.hook.pytask_collect(session=session)
            session.hook.pytask_resolve_dependencies(session=session)
            session.hook.pytask_execute(session=session)

        except CollectionError:
            session.exit_code = ExitCode.COLLECTION_FAILED

        except ResolvingDependenciesError:
            session.exit_code = ExitCode.RESOLVING_DEPENDENCIES_FAILED

        except ExecutionError:
            session.exit_code = ExitCode.FAILED

        except Exception:
            exc_info = sys.exc_info()
            exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
            traceback = Traceback.from_exception(*exc_info)
            console.print(traceback)
            session.exit_code = ExitCode.FAILED

        session.hook.pytask_unconfigure(session=session)

    return session


@click.command(cls=ColoredCommand)
@click.option(
    "--debug-pytask",
    is_flag=True,
    default=None,
    help="Trace all function calls in the plugin framework. [dim]\\[default: False][/]",
)
@click.option(
    "-x",
    "--stop-after-first-failure",
    is_flag=True,
    default=None,
    help="Stop after the first failure.",
)
@click.option("--max-failures", default=None, help="Stop after some failures.")
@click.option(
    "--show-errors-immediately",
    is_flag=True,
    default=None,
    help="Print errors with tracebacks as soon as the task fails.",
)
@click.option(
    "--show-traceback/--show-no-traceback",
    type=bool,
    default=None,
    help=(
        "Choose whether tracebacks should be displayed or not. "
        "[dim]\\[default: True][/]"
    ),
)
@click.option("--dry-run", type=bool, is_flag=True, help="Perform a dry-run.")
def build(**config_from_cli: Any) -> NoReturn:
    """Collect tasks, execute them and report the results.

    This is pytask's default command. pytask collects tasks from the given paths or the
    current working directory, executes them and reports the results.

    """
    config_from_cli["command"] = "build"
    session = main(config_from_cli)
    sys.exit(session.exit_code)
