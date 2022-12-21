"""Contains common parameters for the commands of the command line interface."""
from __future__ import annotations

from pathlib import Path

import click
from _pytask.config import hookimpl
from _pytask.config_utils import set_defaults_from_config


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
        "A pattern to ignore files or directories. For example, task_example.py or "
        "src/*."
    ),
    default=[],
)
"""click.Option: An option for the --ignore flag."""


_PATH_ARGUMENT = click.Argument(
    ["paths"],
    nargs=-1,
    type=click.Path(exists=True, resolve_path=True),
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
    help="Use file, vscode, pycharm or a custom url scheme to add URLs to task "
    "ids to quickly jump to the task definition. Use no_link to disable URLs.",
)
"""click.Option: An option to embed URLs in task ids."""


@hookimpl(trylast=True)
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Register general markers."""
    for command in ("build", "clean", "collect", "dag", "profile"):
        cli.commands[command].params.append(_PATH_ARGUMENT)
    for command in ("build", "clean", "collect", "dag", "markers", "profile"):
        cli.commands[command].params.append(_CONFIG_OPTION)
    for command in ("build", "clean", "collect", "profile"):
        cli.commands[command].params.extend([_IGNORE_OPTION, _EDITOR_URL_SCHEME_OPTION])
    for command in ("build",):
        cli.commands[command].params.append(_VERBOSE_OPTION)
