"""Implements the command line interface."""

from __future__ import annotations

from typing import Any

import click
from packaging.version import parse as parse_version

from _pytask.click import ColoredGroup
from _pytask.pluginmanager import storage
from _pytask.settings import SettingsBuilder
from _pytask.settings import create_settings_loaders

_CONTEXT_SETTINGS: dict[str, Any] = {
    "help_option_names": ("-h", "--help"),
    "show_default": True,
}


if parse_version(click.__version__) >= parse_version("8"):  # pragma: no cover
    _VERSION_OPTION_KWARGS = {"package_name": "pytask"}
else:  # pragma: no cover
    _VERSION_OPTION_KWARGS = {}


def _extend_command_line_interface() -> dict[str, SettingsBuilder]:
    """Add parameters from plugins to the commandline interface."""
    pm = storage.create()
    settings_builders: dict[str, SettingsBuilder] = {}
    pm.hook.pytask_extend_command_line_interface.call_historic(
        kwargs={"settings_builders": settings_builders}
    )
    return settings_builders


@click.group(
    cls=ColoredGroup,
    context_settings=_CONTEXT_SETTINGS,
    default="build",
    default_if_no_args=True,
)
@click.version_option(**_VERSION_OPTION_KWARGS)
def cli() -> None:
    """Manage your tasks with pytask."""


settings_builders = _extend_command_line_interface()
settings_loaders = create_settings_loaders()

for settings_builder in settings_builders.values():
    command = settings_builder.build_command(settings_loaders)
    cli.add_command(command)
