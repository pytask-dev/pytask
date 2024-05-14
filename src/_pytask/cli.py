"""Implements the command line interface."""

from __future__ import annotations

import sys
from typing import Any

import click
from packaging.version import parse as parse_version

from _pytask.click import ColoredCommand
from _pytask.click import ColoredGroup
from _pytask.console import console
from _pytask.pluginmanager import storage
from _pytask.settings_utils import SettingsBuilder
from _pytask.traceback import Traceback

_CONTEXT_SETTINGS: dict[str, Any] = {
    "help_option_names": ("-h", "--help"),
    "show_default": True,
}


if parse_version(click.__version__) >= parse_version("8"):  # pragma: no cover
    _VERSION_OPTION_KWARGS = {"package_name": "pytask"}
else:  # pragma: no cover
    _VERSION_OPTION_KWARGS = {}


def _extend_command_line_interface() -> SettingsBuilder:
    """Add parameters from plugins to the commandline interface."""
    pm = storage.create()
    settings_builder = SettingsBuilder()
    pm.hook.pytask_extend_command_line_interface.call_historic(
        kwargs={"settings_builder": settings_builder}
    )
    return settings_builder


settings_builder = _extend_command_line_interface()
decorator = settings_builder.build_decorator()


@click.group(
    cls=ColoredGroup,
    context_settings=_CONTEXT_SETTINGS,
    default="build",
    default_if_no_args=True,
)
@click.version_option(**_VERSION_OPTION_KWARGS)
def cli() -> None:
    """Manage your tasks with pytask."""


try:
    for name, func in settings_builder.commands.items():
        command = click.command(name=name, cls=ColoredCommand)(decorator(func))
        command.params.extend(settings_builder.arguments)
        cli.add_command(command)
except Exception:  # noqa: BLE001
    traceback = Traceback(sys.exc_info(), show_locals=False)
    console.print(traceback)
