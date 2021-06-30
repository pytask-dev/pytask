"""Add general logging capabilities."""
import platform
import sys
from typing import Any
from typing import List
from typing import Tuple

import _pytask
import click
import pluggy
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value


@hookimpl
def pytask_extend_command_line_interface(cli):
    show_locals_option = click.Option(
        ["--show-locals"],
        is_flag=True,
        default=None,
        help="Show local variables in tracebacks.",
    )
    cli.commands["build"].params.append(show_locals_option)


@hookimpl
def pytask_parse_config(config, config_from_file, config_from_cli):
    config["show_locals"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="show_locals",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )


@hookimpl
def pytask_log_session_header(session):
    """Log the header of a pytask session."""
    console.rule("Start pytask session", style=None)
    console.print(
        f"Platform: {sys.platform} -- Python {platform.python_version()}, "
        f"pytask {_pytask.__version__}, pluggy {pluggy.__version__}"
    )
    console.print(f"Root: {session.config['root']}")
    if session.config["config"] is not None:
        console.print(f"Configuration: {session.config['config']}")

    plugin_info = session.config["pm"].list_plugin_distinfo()
    if plugin_info:
        formatted_plugins_w_versions = ", ".join(
            _format_plugin_names_and_versions(plugin_info)
        )
        console.print(f"Plugins: {formatted_plugins_w_versions}")


def _format_plugin_names_and_versions(plugininfo) -> List[str]:
    """Format name and version of loaded plugins."""
    values: List[str] = []
    for _, dist in plugininfo:
        # Gets us name and version!
        name = f"{dist.project_name}-{dist.version}"
        # Questionable convenience, but it keeps things short.
        if name.startswith("pytask-"):
            name = name[7:]
        # We decided to print python package names they can have more than one plugin.
        if name not in values:
            values.append(name)
    return values


@hookimpl
def pytask_log_session_footer(
    infos: List[Tuple[Any]], duration: float, color: str
) -> str:
    """Format the footer of the log message."""
    message = f"[{color}]"
    message += _style_infos(infos)
    message += f" in {duration}s"

    console.rule(message, style=color)


def _style_infos(infos: List[Tuple[Any]]) -> str:
    """Style infos.

    Example
    -------
    >>> m = _style_infos([(1, "a", "green"), (2, "b", "red"), (0, "c", "yellow")])
    >>> print(m)
    [green]1 a[/], [red]2 b[/]

    """
    message = []
    for value, description, color in infos:
        if value:
            message.append(f"[{color}]{value} {description}[/]")
    return ", ".join(message)
