import sys

import click
from _pytask.config import hookimpl
from _pytask.pluginmanager import get_plugin_manager
from click_default_group import DefaultGroup


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def extend_command_line_interface(command):
    """Add parameters from plugins to the commandline interface."""
    pm = _prepare_plugin_manager()
    pm.hook.pytask_add_parameters_to_cli(command=command)

    return command


def _prepare_plugin_manager():
    pm = get_plugin_manager()
    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks(pm=pm)
    return pm


@hookimpl
def pytask_add_hooks(pm):
    from _pytask import clean
    from _pytask import collect
    from _pytask import config
    from _pytask import database
    from _pytask import debugging
    from _pytask import execute
    from _pytask import logging
    from _pytask import build
    from _pytask import mark
    from _pytask import parametrize
    from _pytask import resolve_dependencies
    from _pytask import skipping

    pm.register(clean)
    pm.register(collect)
    pm.register(config)
    pm.register(database)
    pm.register(debugging)
    pm.register(execute)
    pm.register(logging)
    pm.register(build)
    pm.register(parametrize)
    pm.register(resolve_dependencies)
    pm.register(skipping)
    pm.register(mark)


@click.group(
    cls=DefaultGroup,
    context_settings=CONTEXT_SETTINGS,
    default="build",
    default_if_no_args=True,
)
@click.version_option()
def cli():
    pass


extend_command_line_interface(cli)
