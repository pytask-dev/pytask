import sys
from pathlib import Path

import click
import pytask.mark.cli
from pytask.pluginmanager import get_plugin_manager


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def add_parameters(func):
    """Add parameters from plugins to the commandline interface."""
    pm = get_plugin_manager()
    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks(pm=pm)
    pm.hook.pytask_add_parameters_to_cli(command=func)

    # Hack to pass the plugin manager via a hidden option to the ``config_from_cli``.
    func.params.append(click.Option(["--pm"], default=pm, hidden=True))

    return func


@pytask.hookimpl
def pytask_add_hooks(pm):
    """Add some hooks and plugins.

    This hook implementation registers only plugins which extend the command line
    interface or patch the main entry-point :func:`pytask.hookspecs.pytask_main`.

    """
    from pytask import database
    from pytask import debugging
    from pytask import main
    from pytask.mark import cli as mark_cli

    pm.register(database)
    pm.register(debugging)
    pm.register(main)
    pm.register(mark_cli)


def _to_path(ctx, param, value):  # noqa: U100
    """Callback for :class:`click.Argument` or :class:`click.Option`."""
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
        click.Option(
            ["--debug-pytask"],
            is_flag=True,
            help="Debug pytask by tracing all hook calls.",
        ),
    ]
    command.params.extend(additional_parameters)


@add_parameters
@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def pytask(**config_from_cli):
    """Command-line interface for pytask."""
    pm = config_from_cli["pm"]
    session = pm.hook.pytask_main(config_from_cli=config_from_cli)
    sys.exit(session.exit_code)
