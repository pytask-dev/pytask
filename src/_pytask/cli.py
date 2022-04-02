"""Implements the command line interface."""
from __future__ import annotations

import sys
from typing import Any

import attrs
import click
import pluggy
import typed_settings as ts
from _pytask.click import ColoredCommand
from _pytask.click import ColoredGroup
from _pytask.config import hookimpl
from _pytask.pluginmanager import get_plugin_manager
from _pytask.typed_settings import file_loader
from _pytask.typed_settings import type_handler, converter
from packaging.version import parse as parse_version


_CONTEXT_SETTINGS: dict[str, Any] = {"help_option_names": ("-h", "--help")}


if parse_version(click.__version__) < parse_version("8"):
    _VERSION_OPTION_KWARGS: dict[str, Any] = {}
else:
    _VERSION_OPTION_KWARGS = {"package_name": "pytask"}


def _extend_command_line_interface(cli: click.Group) -> click.Group:
    """Add parameters from plugins to the commandline interface."""
    pm = _prepare_plugin_manager()
    pm.hook.pytask_extend_command_line_interface(cli=cli)
    return cli


def _prepare_plugin_manager() -> pluggy.PluginManager:
    """Prepare the plugin manager."""
    pm = get_plugin_manager()
    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks(pm=pm)
    return pm


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


def cli(*args, main_settings) -> None:  # noqa: U100
    """Manage your tasks with pytask."""
    pass


def _make_class(name: str, options: dict[str, Any], properties: dict[str, Any]) -> type:
    class_ = attrs.make_class(name, options)

    for name, property_ in properties.items():
        setattr(class_, name, property(property_))

    return class_


cmd_name_to_info = {"main": {"cmd": cli, "options": {}}}

_extend_command_line_interface(cmd_name_to_info)


cmd_to_settings = {
    name: _make_class(
        name.title() + "Settings", info["options"], info.get("properties", {})
    )
    for name, info in cmd_name_to_info.items()
}


cli = click.version_option(**_VERSION_OPTION_KWARGS)(
    click.group(
        cls=ColoredGroup,
        context_settings=_CONTEXT_SETTINGS,
        default="build",
        default_if_no_args=True,
    )(
        ts.click_options(
            cmd_to_settings["main"],
            loaders=[file_loader],
            converter=converter,
            argname="main_settings",
            type_handler=type_handler,
        )(click.pass_obj(cli))
    )
)


for name in cmd_name_to_info:
    if name == "main":
        continue

    cli.command(cls=ColoredCommand,)(  # Uncomment to see the full name of switches.
        ts.pass_settings(argname="main_settings")(
            ts.click_options(
                cmd_to_settings[name],
                loaders=[file_loader],
                converter=converter,
                argname=f"{name}_settings",
                type_handler=type_handler,
            )(cmd_name_to_info[name]["cmd"])
        )
    )
