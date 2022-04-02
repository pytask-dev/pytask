"""Contains common parameters for the commands of the command line interface."""
from __future__ import annotations

import glob
import warnings
from pathlib import Path
from typing import List
from typing import Union

import click
from _pytask.attrs import convert_to_none_or_type
from _pytask.config import hookimpl
from _pytask.console import IS_WINDOWS_TERMINAL
from _pytask.shared import falsy_to_none_callback
from _pytask.shared import to_list
from _pytask.typed_settings import option
from _pytask.models import PathType


_CONFIG_OPTION = option(
    converter=convert_to_none_or_type(Path),
    default=None,
    help="Path to configuration file.",
    param_decls=("-c", "--config"),
    type=str,
)
"""option: An option for the --config flag."""


_IGNORE_OPTION = option(
    converter=convert_to_none_or_type(str),
    default=None,
    help=(
        "A pattern to ignore files or directories. For example, task_example.py or "
        "src/*."
    ),
    type=str,
)
"""option: An option for the --ignore flag."""


def _markers_converter(string: str | None) -> dict[str, str]:
    """Read marker descriptions from configuration file."""
    if string is None:
        return {}

    # Split by newlines and remove empty strings.
    lines = filter(lambda x: bool(x), string.split("\n"))
    mapping = {}
    for line in lines:
        try:
            key, value = line.split(":")
        except ValueError as e:
            key = line
            value = ""
            if not key.isidentifier():
                raise ValueError(
                    f"{key} is not a valid Python name and cannot be used as a marker."
                ) from e

        mapping[key.strip()] = value.strip()

    return mapping


_MARKERS_OPTION = option(
    converter=_markers_converter,
    default=None,
    hidden=True,
    type=str,
)


def _path_callback(ctx, param, value):  # noqa: U100
    """Convert input to :obj:`None` or absolute paths."""
    if not value:
        return None
    else:
        paths = []
        for i in value:
            path = Path(i)
            if not path.is_absolute():
                path = Path.cwd() / path
            paths.append(path.resolve())
        return paths


_PATH_ARGUMENT = click.argument(
    "paths", nargs=-1, type=click.Path(exists=True), callback=_path_callback
)
"""click.Argument: An argument for paths."""


def _to_paths(x: Any | None) -> list[Path]:
    """Parse paths."""
    if x is not None:
        paths = [Path(p) for p in to_list(x)]
        paths = [
            Path(p).resolve() for path in paths for p in glob.glob(path.as_posix())
        ]
        out = paths
    else:
        out = []
    return out


# Todo: Does not read paths from file.
_PATH_OPTION = option(
    # converter=_to_paths,
    default=[Path.cwd()],
    hidden=True,
)


_VERBOSE_OPTION = option(
    default=1,
    type=int,
    param_decls=("-v", "--verbose"),
    help="Make pytask verbose (>= 0) or quiet (< 0) [dim]\\[default: 1][/]",
)
"""click.Option: An option to control pytask's verbosity."""


def _editor_url_scheme_converter(x: str) -> str:
    if x not in ["no_link", "file"] and IS_WINDOWS_TERMINAL:
        warnings.warn(
            "Windows Terminal does not support url schemes to applications, yet. "
            "See https://github.com/pytask-dev/pytask/issues/171 for more information. "
            "Resort to `editor_url_scheme='file'`."
        )
        return "file"


_EDITOR_URL_SCHEME_OPTION = option(
    converter=_editor_url_scheme_converter,
    default="file",
    type=str,
    help="Use file, vscode, pycharm or a custom url scheme to add URLs to task "
    "ids to quickly jump to the task definition. Use no_link to disable URLs. "
    "[dim]\\[default: file][/]",
)
"""click.Option: An option to embed URLs in task ids."""


_CHECK_CASING_OF_PATHS_OPTION = option(
    default=True,
    help="Raises error if paths are not stated with the correct capitalisation.",
    hidden=True,
    type=bool,
)


_TASK_FILES_OPTION = option(
    default=["task_*.py"],
    help="Patterns which match files containing tasks.",
    hidden=True,
    type=List[str],
)


@hookimpl(trylast=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Register general markers."""
    for name, option in [
        ("check_casing_of_paths", _CHECK_CASING_OF_PATHS_OPTION),
        ("task_files", _TASK_FILES_OPTION),
    ]:
        cli["main"]["options"][name] = option
    for command in ["build", "clean", "collect", "markers", "profile"]:
        cli[command]["options"]["config"] = _CONFIG_OPTION
        cli[command]["options"]["markers"] = _MARKERS_OPTION
    for command in ["build", "clean", "collect", "profile"]:
        cli[command]["options"]["ignore"] = _IGNORE_OPTION
        cli[command]["options"]["editor_url_scheme"] = _EDITOR_URL_SCHEME_OPTION
    for command in ["build", "clean", "collect", "dag", "profile"]:
        _PATH_ARGUMENT(cli[command]["cmd"])
        cli[command]["options"]["paths"] = _PATH_OPTION
    for command in ["build"]:
        cli[command]["options"]["verbose"] = _VERBOSE_OPTION
