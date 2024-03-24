"""Contains common parameters for the commands of the command line interface."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click
import typed_settings as ts
from click import Context
from pluggy import PluginManager

from _pytask.pluginmanager import hookimpl

if TYPE_CHECKING:
    from _pytask.settings import SettingsBuilder


def _path_callback(
    ctx: Context,  # noqa: ARG001
    param: click.Parameter,  # noqa: ARG001
    value: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Convert paths to Path objects."""
    return value or (Path.cwd(),)


@ts.settings
class Common:
    """Common settings for the command line interface."""

    paths: tuple[Path, ...] = ts.option(
        factory=tuple,
        click={
            "param_decls": ["--paths"],
            "type": click.Path(exists=True, resolve_path=True, path_type=Path),
            "multiple": True,
            "callback": _path_callback,
            "hidden": True,
        },
    )
    pm: PluginManager | None = ts.option(default=None, click={"hidden": True})


_PATH_ARGUMENT = click.Argument(
    ["paths"],
    nargs=-1,
    type=click.Path(exists=True, resolve_path=True, path_type=Path),
)
"""click.Argument: An argument for paths."""


@hookimpl(trylast=True)
def pytask_extend_command_line_interface(
    settings_builders: dict[str, SettingsBuilder],
) -> None:
    """Register general markers."""
    for settings_builder in settings_builders.values():
        settings_builder.arguments.append(_PATH_ARGUMENT)
        settings_builder.option_groups["common"] = Common()
