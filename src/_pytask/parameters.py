"""Contains common parameters for the commands of the command line interface."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Iterable

import click
import typed_settings as ts
from click import Context

from _pytask.path import import_path
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import register_hook_impls_from_modules
from _pytask.pluginmanager import storage

if TYPE_CHECKING:
    from pluggy import PluginManager

    from _pytask.settings import SettingsBuilder


def _hook_module_callback(
    ctx: Context,
    name: str,  # noqa: ARG001
    value: tuple[str, ...],
) -> Iterable[str | Path]:
    """Register the user's hook modules from the configuration file."""
    if not value:
        return value

    parsed_modules = []
    for module_name in value:
        if module_name.endswith(".py"):
            path = Path(module_name)
            if ctx.params["config"]:
                path = ctx.params["config"].parent.joinpath(path).resolve()
            else:
                path = Path.cwd().joinpath(path).resolve()

            if not path.exists():
                msg = (
                    f"The hook module {path} does not exist. "
                    "Please provide a valid path."
                )
                raise click.BadParameter(msg)
            module = import_path(path, ctx.params["root"])
            parsed_modules.append(module.__name__)
        else:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                msg = (
                    f"The hook module {module_name!r} is not importable. "
                    "Please provide a valid module name."
                )
                raise click.BadParameter(msg)
            parsed_modules.append(module_name)

    # If there are hook modules, we register a hook implementation to add them.
    # ``pytask_add_hooks`` is a historic hook specification, so even command line
    # options can be added.
    if parsed_modules:

        class HookModule:
            @staticmethod
            @hookimpl
            def pytask_add_hooks(pm: PluginManager) -> None:
                """Add hooks."""
                register_hook_impls_from_modules(pm, parsed_modules)

        pm = storage.get()
        pm.register(HookModule)

    return parsed_modules


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

    editor_url_scheme: str = ts.option(
        default="file",
        click={"param_decls": ["--editor-url-scheme"]},
        help=(
            "Use file, vscode, pycharm or a custom url scheme to add URLs to task "
            "ids to quickly jump to the task definition. Use no_link to disable URLs."
        ),
    )
    ignore: tuple[str, ...] = ts.option(
        factory=tuple,
        help=(
            "A pattern to ignore files or directories. Refer to 'pathlib.Path.match' "
            "for more info."
        ),
        click={"param_decls": ["--ignore"], "multiple": True},
    )
    verbose: int = ts.option(
        default=1,
        help="Make pytask verbose (>= 0) or quiet (= 0).",
        click={
            "param_decls": ["-v", "--verbose"],
            "type": click.IntRange(0, 2),
            "count": True,
        },
    )
    hook_module: tuple[str, ...] = ts.option(
        factory=list,
        help="Path to a Python module that contains hook implementations.",
        click={
            "param_decls": ["--hook-module"],
            "multiple": True,
            "is_eager": True,
            "callback": _hook_module_callback,
        },
    )
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
