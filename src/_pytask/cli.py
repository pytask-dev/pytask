"""Implements the command line interface."""
import sys
from typing import Any
from typing import Dict

import click
import pluggy
from _pytask.config import hookimpl
from _pytask.pluginmanager import get_plugin_manager
from click_default_group import DefaultGroup
from packaging.version import parse as parse_version


_CONTEXT_SETTINGS: Dict[str, Any] = {"help_option_names": ["-h", "--help"]}


if parse_version(click.__version__) < parse_version("8"):
    _VERSION_OPTION_KWARGS: Dict[str, Any] = {}
else:
    _VERSION_OPTION_KWARGS = {"package_name": "pytask"}


def _extend_command_line_interface(cli: click.Group) -> click.Group:
    """Add parameters from plugins to the commandline interface."""
    pm = _prepare_plugin_manager()
    pm.hook.pytask_extend_command_line_interface(cli=cli)
    _sort_options_for_each_command_alphabetically(cli)
    return cli


def _prepare_plugin_manager() -> pluggy.PluginManager:
    """Prepare the plugin manager."""
    pm = get_plugin_manager()
    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks(pm=pm)
    return pm


def _sort_options_for_each_command_alphabetically(cli: click.Group) -> None:
    """Sort command line options and arguments for each command alphabetically."""
    for command in cli.commands:
        cli.commands[command].params = sorted(
            cli.commands[command].params, key=lambda x: x.name
        )


@hookimpl
def pytask_add_hooks(pm: pluggy.PluginManager) -> None:
    """Add hooks."""
    from _pytask import build
    from _pytask import capture
    from _pytask import clean
    from _pytask import collect
    from _pytask import collect_command
    from _pytask import config
    from _pytask import database
    from _pytask import debugging
    from _pytask import execute
    from _pytask import graph
    from _pytask import live
    from _pytask import logging
    from _pytask import mark
    from _pytask import parameters
    from _pytask import parametrize
    from _pytask import persist
    from _pytask import profile
    from _pytask import resolve_dependencies
    from _pytask import skipping
    from _pytask import task

    pm.register(build)
    pm.register(capture)
    pm.register(clean)
    pm.register(collect)
    pm.register(collect_command)
    pm.register(config)
    pm.register(database)
    pm.register(debugging)
    pm.register(execute)
    pm.register(graph)
    pm.register(live)
    pm.register(logging)
    pm.register(mark)
    pm.register(parameters)
    pm.register(parametrize)
    pm.register(persist)
    pm.register(profile)
    pm.register(resolve_dependencies)
    pm.register(skipping)
    pm.register(task)


@click.group(
    cls=DefaultGroup,
    context_settings=_CONTEXT_SETTINGS,
    default="build",
    default_if_no_args=True,
)
@click.version_option(**_VERSION_OPTION_KWARGS)
def cli() -> None:
    """The command line interface of pytask."""
    pass


_extend_command_line_interface(cli)
