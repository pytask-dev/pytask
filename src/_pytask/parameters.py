"""Contains common parameters for the commands of the command line interface."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import click
from click import Context
from sqlalchemy.engine import URL
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from _pytask.config_utils import set_defaults_from_config
from _pytask.path import import_path
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import register_hook_impls_from_modules
from _pytask.pluginmanager import storage

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pluggy import PluginManager


_CONFIG_OPTION = click.Option(
    ["-c", "--config"],
    callback=set_defaults_from_config,
    is_eager=True,
    expose_value=False,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
        path_type=Path,
        resolve_path=True,
    ),
    help="Path to configuration file.",
)
"""click.Option: An option for the --config flag."""


_IGNORE_OPTION = click.Option(
    ["--ignore"],
    type=str,
    multiple=True,
    help=(
        "A pattern to ignore files or directories. Refer to 'pathlib.Path.match' "
        "for more info."
    ),
    default=[],
)
"""click.Option: An option for the --ignore flag."""


_PATH_ARGUMENT = click.Argument(
    ["paths"],
    nargs=-1,
    type=click.Path(exists=True, resolve_path=True, path_type=Path),
    is_eager=True,
)
"""click.Argument: An argument for paths."""


_VERBOSE_OPTION = click.Option(
    ["-v", "--verbose"],
    type=click.IntRange(0, 2),
    default=1,
    help="Make pytask verbose (>= 0) or quiet (= 0).",
)
"""click.Option: An option to control pytask's verbosity."""


_EDITOR_URL_SCHEME_OPTION = click.Option(
    ["--editor-url-scheme"],
    default="file",
    help=(
        "Use file, vscode, pycharm or a custom url scheme to add URLs to task "
        "ids to quickly jump to the task definition. Use no_link to disable URLs."
    ),
)
"""click.Option: An option to embed URLs in task ids."""


def _database_url_callback(
    ctx: Context,  # noqa: ARG001
    name: str,  # noqa: ARG001
    value: str | None,
) -> URL | None:
    """Check the url for the database."""
    # Since sqlalchemy v2.0.19, we need to shortcircuit here.
    if value is None:
        return None

    try:
        return make_url(value)
    except ArgumentError:
        msg = (
            "The 'database_url' must conform to sqlalchemy's url standard: "
            "https://docs.sqlalchemy.org/en/latest/core/engines.html#backend-specific-urls."
        )
        raise click.BadParameter(msg) from None


_DATABASE_URL_OPTION = click.Option(
    ["--database-url"],
    type=str,
    help="Url to the database.",
    default=None,
    show_default="sqlite:///.../.pytask/pytask.sqlite3",
    callback=_database_url_callback,
)


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


_HOOK_MODULE_OPTION = click.Option(
    ["--hook-module"],
    type=str,
    help="Path to a Python module that contains hook implementations.",
    multiple=True,
    is_eager=True,
    callback=_hook_module_callback,
)


@hookimpl(trylast=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Register general markers."""
    for command in ("build", "clean", "collect", "dag", "profile"):
        cli.commands[command].params.extend((_DATABASE_URL_OPTION,))
    for command in ("build", "clean", "collect", "dag", "markers", "profile"):
        cli.commands[command].params.extend(
            (_CONFIG_OPTION, _HOOK_MODULE_OPTION, _PATH_ARGUMENT)
        )
    for command in ("build", "clean", "collect", "profile"):
        cli.commands[command].params.extend([_IGNORE_OPTION, _EDITOR_URL_SCHEME_OPTION])
    for command in ("build",):
        cli.commands[command].params.append(_VERBOSE_OPTION)
