"""Implement the build command."""
import sys
import traceback

import click
from _pytask.config import hookimpl
from _pytask.enums import ExitCode
from _pytask.exceptions import CollectionError
from _pytask.exceptions import ConfigurationError
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.pluginmanager import get_plugin_manager
from _pytask.session import Session


@hookimpl(tryfirst=True)
def pytask_extend_command_line_interface(cli):
    """Extend the command line interface."""
    cli.add_command(build)


def main(config_from_cli):
    """Run pytask.

    This is the main command to run pytask which usually receives kwargs from the
    command line interface. It can also be used to run pytask interactively. Pass
    configuration in a dictionary.

    Parameters
    ----------
    config_from_cli : dict
        A dictionary with options passed to pytask. In general, this dictionary holds
        the information passed via the command line interface.

    Returns
    -------
    session : pytask.session.Session
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
        traceback.print_exception(*sys.exc_info())
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
            traceback.print_exception(*sys.exc_info())
            session.exit_code = ExitCode.FAILED

    return session


@click.command()
@click.option(
    "--debug-pytask",
    is_flag=True,
    default=None,
    help="Trace all function calls in the plugin framework.  [default: False]",
)
@click.option(
    "-x",
    "--stop-after-first-failure",
    is_flag=True,
    default=None,
    help="Stop after the first failure.",
)
@click.option("--max-failures", default=None, help="Stop after some failures.")
def build(**config_from_cli):
    """Collect and execute tasks and report the results.

    This is the default command of pytask which searches given paths or the current
    working directory for tasks to execute them. A report informs you on the results.

    """
    config_from_cli["command"] = "build"
    session = main(config_from_cli)
    sys.exit(session.exit_code)
