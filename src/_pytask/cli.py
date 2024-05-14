"""Implements the command line interface."""

from __future__ import annotations

from typing import Any

import click
from packaging.version import parse as parse_version

from _pytask.click import ColoredGroup
from _pytask.pluginmanager import storage

_CONTEXT_SETTINGS: dict[str, Any] = {
    "help_option_names": ("-h", "--help"),
    "show_default": True,
}


if parse_version(click.__version__) >= parse_version("8"):  # pragma: no cover
    _VERSION_OPTION_KWARGS = {"package_name": "pytask"}
else:  # pragma: no cover
    _VERSION_OPTION_KWARGS = {}


def _extend_command_line_interface(cli: click.Group) -> click.Group:
    """Add parameters from plugins to the commandline interface."""
    pm = storage.create()
    pm.hook.pytask_extend_command_line_interface.call_historic(kwargs={"cli": cli})
    _sort_options_for_each_command_alphabetically(cli)
    return cli


def _sort_options_for_each_command_alphabetically(cli: click.Group) -> None:
    """Sort command line options and arguments for each command alphabetically."""
    for command in cli.commands:
        cli.commands[command].params = sorted(
            cli.commands[command].params, key=lambda x: x.opts[0].replace("-", "")
        )


@click.group(
    cls=ColoredGroup,
    context_settings=_CONTEXT_SETTINGS,
    default="build",
    default_if_no_args=True,
)
@click.version_option(**_VERSION_OPTION_KWARGS)
def cli() -> None:
    """Manage your tasks with pytask."""


_extend_command_line_interface(cli)


DEFAULTS_FROM_CLI = {
    option.name: option.default
    for command in cli.commands.values()
    for option in command.params
}
