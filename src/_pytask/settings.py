from __future__ import annotations

import importlib.util
from enum import Enum
from pathlib import Path
from typing import Iterable

import click
import typed_settings as ts
from click import BadParameter
from click import Context
from pluggy import PluginManager
from sqlalchemy.engine import URL
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from _pytask.capture_utils import CaptureMethod
from _pytask.capture_utils import ShowCapture
from _pytask.click import EnumChoice
from _pytask.path import import_path
from _pytask.pluginmanager import hookimpl
from _pytask.pluginmanager import register_hook_impls_from_modules
from _pytask.pluginmanager import storage


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


@ts.settings
class Build:
    stop_after_first_failure: bool = ts.option(
        default=False,
        click={"param_decls": ("-x", "--stop-after-first-failure"), "is_flag": True},
        help="Stop after the first failure.",
    )
    max_failures: float = ts.option(
        default=float("inf"),
        click={"param_decls": ("--max-failures",)},
        help="Stop after some failures.",
    )
    show_errors_immediately: bool = ts.option(
        default=False,
        click={"param_decls": ("--show-errors-immediately",), "is_flag": True},
        help="Show errors with tracebacks as soon as the task fails.",
    )
    show_traceback: bool = ts.option(
        default=True,
        click={"param_decls": ("--show-traceback", "--show-no-traceback")},
        help="Choose whether tracebacks should be displayed or not.",
    )
    dry_run: bool = ts.option(
        default=False,
        click={"param_decls": ("--dry-run",), "is_flag": True},
        help="Perform a dry-run.",
    )
    force: bool = ts.option(
        default=False,
        click={"param_decls": ("-f", "--force"), "is_flag": True},
        help="Execute a task even if it succeeded successfully before.",
    )
    check_casing_of_paths: bool = ts.option(
        default=True,
        click={"param_decls": ("--check-casing-of-paths",), "hidden": True},
    )


class _ExportFormats(Enum):
    NO = "no"
    JSON = "json"
    CSV = "csv"


@ts.settings
class Profile:
    export: _ExportFormats = ts.option(
        default=_ExportFormats.NO,
        help="Export the profile in the specified format.",
    )


class _CleanMode(Enum):
    DRY_RUN = "dry-run"
    FORCE = "force"
    INTERACTIVE = "interactive"


@ts.settings
class Clean:
    directories: bool = ts.option(
        default=False,
        help="Remove whole directories.",
        click={"is_flag": True, "param_decls": ["-d", "--directories"]},
    )
    exclude: tuple[str, ...] = ts.option(
        factory=tuple,
        help="A filename pattern to exclude files from the cleaning process.",
        click={
            "multiple": True,
            "metavar": "PATTERN",
            "param_decls": ["-e", "--exclude"],
        },
    )
    mode: _CleanMode = ts.option(
        default=_CleanMode.DRY_RUN,
        help=(
            "Choose 'dry-run' to print the paths of files/directories which would be "
            "removed, 'interactive' for a confirmation prompt for every path, and "
            "'force' to remove all unknown paths at once."
        ),
        click={"type": EnumChoice(_CleanMode), "param_decls": ["-m", "--mode"]},
    )
    quiet: bool = ts.option(
        default=False,
        help="Do not print the names of the removed paths.",
        click={"is_flag": True, "param_decls": ["-q", "--quiet"]},
    )


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
        raise BadParameter(msg) from None


@ts.settings
class Database:
    """Settings for the database."""

    database_url: str = ts.option(
        default=None,
        help="Url to the database.",
        click={
            "show_default": "sqlite:///.../.pytask/pytask.sqlite3",
            "callback": _database_url_callback,
        },
    )


@ts.settings
class Markers:
    """Settings for markers."""

    strict_markers: bool = ts.option(
        default=False,
        click={"param_decls": ["--strict-markers"], "is_flag": True},
        help="Raise errors for unknown markers.",
    )
    markers: dict[str, str] = ts.option(factory=dict, click={"hidden": True})
    marker_expression: str = ts.option(
        default="",
        click={
            "param_decls": ["-m", "marker_expression"],
            "metavar": "MARKER_EXPRESSION",
        },
        help="Select tasks via marker expressions.",
    )
    expression: str = ts.option(
        default="",
        click={"param_decls": ["-k", "expression"], "metavar": "EXPRESSION"},
        help="Select tasks via expressions on task ids.",
    )


@ts.settings
class Settings:
    debug_pytask: bool = ts.option(
        default=False,
        click={"param_decls": ("--debug-pytask",), "is_flag": True},
        help="Trace all function calls in the plugin framework.",
    )
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
    config_file: Path | None = None


@ts.settings
class Capture:
    """Settings for capturing."""

    capture: CaptureMethod = ts.option(
        default=CaptureMethod.FD,
        click={"param_decls": ["--capture"]},
        help="Per task capturing method.",
    )
    s: bool = ts.option(
        default=False,
        click={"param_decls": ["-s"], "is_flag": True},
        help="Shortcut for --capture=no.",
    )
    show_capture: ShowCapture = ts.option(
        default=ShowCapture.ALL,
        click={"param_decls": ["--show-capture"]},
        help="Choose which captured output should be shown for failed tasks.",
    )
