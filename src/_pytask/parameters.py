"""Contains common parameters for the commands of the command line interface."""
from __future__ import annotations
from pathlib import Path
import click
from _pytask.config import hookimpl
from _pytask.shared import falsy_to_none_callback
from _pytask.typed_settings import option
from _pytask.attrs import convert_to_none_or_type


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


_VERBOSE_OPTION = option(
    default=0,
    type=int,
    param_decls=("-v", "--verbose"),
    help="Make pytask verbose (>= 0) or quiet (< 0) [dim]\\[default: 0][/]",
)
"""click.Option: An option to control pytask's verbosity."""


_EDITOR_URL_SCHEME_OPTION = option(
    default="file",
    type=str,
    help="Use file, vscode, pycharm or a custom url scheme to add URLs to task "
    "ids to quickly jump to the task definition. Use no_link to disable URLs. "
    "[dim]\\[default: file][/]",
)
"""click.Option: An option to embed URLs in task ids."""


@hookimpl(trylast=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Register general markers."""
    for command in ["build", "clean", "collect", "markers", "profile"]:
        cli[command]["options"]["config"] = _CONFIG_OPTION
    for command in ["build", "clean", "collect", "profile"]:
        cli[command]["options"]["ignore"] = _IGNORE_OPTION
        cli[command]["options"]["editor_url_scheme"] = _EDITOR_URL_SCHEME_OPTION
    for command in ["build", "clean", "collect", "dag", "profile"]:
        _PATH_ARGUMENT(cli[command]["cmd"])
    for command in ["build"]:
        cli[command]["options"]["verbose"] = _VERBOSE_OPTION
