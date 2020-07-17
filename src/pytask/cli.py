import sys
from pathlib import Path

import click
import pytask
from pytask.main import main
from pytask.pluginmanager import get_plugin_manager


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def add_parameters(func):
    """Add parameters from plugins to the commandline interface."""
    pm = get_plugin_manager()
    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks(pm=pm)
    pm.hook.pytask_add_parameters_to_cli(command=func)

    return func


@pytask.hookimpl
def pytask_add_hooks(pm):
    from pytask import database
    from pytask import debugging

    pm.register(database)
    pm.register(debugging)


def _to_path(ctx, param, value):  # noqa: U100
    return [Path(i).resolve() for i in value]


@pytask.hookimpl
def pytask_add_parameters_to_cli(command):
    additional_parameters = [
        click.Argument(
            ["paths"], nargs=-1, type=click.Path(exists=True), callback=_to_path,
        ),
        click.Option(
            ["--ignore"],
            type=str,
            multiple=True,
            help="Ignore path (globs and multi allowed).",
        ),
        click.Option(["--debug-pytask"], is_flag=True, help="Debug pytask."),
    ]
    command.params.extend(additional_parameters)


@add_parameters
@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def pytask(**config_from_cli):
    """Command-line interface for pytask."""
    session = main(config_from_cli)
    sys.exit(session.exit_code)
