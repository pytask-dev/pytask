import sys
from pathlib import Path

import click
from _pytask.config import hookimpl
from _pytask.pluginmanager import get_plugin_manager


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def add_parameters(command):
    """Add parameters from plugins to the commandline interface."""
    pm = _prepare_plugin_manager()
    pm.hook.pytask_add_parameters_to_cli(command=command)
    # Hack to pass the plugin manager via a hidden option to the ``config_from_cli``.
    command.params.append(click.Option(["--pm"], default=pm, hidden=True))

    return command


def _prepare_plugin_manager():
    pm = get_plugin_manager()
    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks(pm=pm)
    return pm


@hookimpl
def pytask_add_hooks(pm):
    from _pytask import collect
    from _pytask import config
    from _pytask import database
    from _pytask import debugging
    from _pytask import execute
    from _pytask import logging
    from _pytask import main
    from _pytask import parametrize
    from _pytask import resolve_dependencies
    from _pytask import skipping
    from _pytask import mark

    pm.register(collect)
    pm.register(config)
    pm.register(database)
    pm.register(debugging)
    pm.register(execute)
    pm.register(logging)
    pm.register(main)
    pm.register(parametrize)
    pm.register(resolve_dependencies)
    pm.register(skipping)
    pm.register(mark)


def _to_path(ctx, param, value):  # noqa: U100
    """Callback for :class:`click.Argument` or :class:`click.Option`."""
    return [Path(i).resolve() for i in value]


@hookimpl
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
    session = main(config_from_cli)
    sys.exit(session.exit_code)


def main(config_from_cli):
    pm = config_from_cli.get("pm", _prepare_plugin_manager())
    session = pm.hook.pytask_main(config_from_cli=config_from_cli)

    return session
