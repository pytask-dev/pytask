"""Contains common parameters for the commands of the command line interface."""
import click
from _pytask.config import hookimpl
from _pytask.shared import falsy_to_none_callback


_CONFIG_OPTION = click.Option(
    ["-c", "--config"], type=click.Path(exists=True), help="Path to configuration file."
)
"""click.Option: An general option for the --config flag."""

_IGNORE_OPTION = click.Option(
    ["--ignore"],
    type=str,
    multiple=True,
    help=(
        "A pattern to ignore files or directories. For example, ``task_example.py`` or "
        "``src/*``."
    ),
    callback=falsy_to_none_callback,
)
"""click.Option: An general option for the --ignore flag."""


_PATH_ARGUMENT = click.Argument(
    ["paths"], nargs=-1, type=click.Path(exists=True), callback=falsy_to_none_callback
)
"""click.Option: An general paths argument."""


@hookimpl(trylast=True)
def pytask_extend_command_line_interface(cli):
    """Register general markers."""
    for command in ["build", "clean", "collect", "markers"]:
        cli.commands[command].params.append(_CONFIG_OPTION)
    for command in ["build", "clean", "collect"]:
        cli.commands[command].params.append(_IGNORE_OPTION)
    for command in ["build", "clean", "collect"]:
        cli.commands[command].params.append(_PATH_ARGUMENT)
