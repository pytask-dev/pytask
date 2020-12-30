"""Add general logging capabilities."""
import math
import platform
import sys
from typing import Any
from typing import List
from typing import Tuple

import _pytask
import click
import pluggy
from _pytask.config import hookimpl


@hookimpl
def pytask_log_session_header(session):
    """Log the header of a pytask session."""
    tm_width = session.config["terminal_width"]

    click.echo(f"{{:=^{tm_width}}}".format(" Start pytask session "), nl=True)
    click.echo(
        f"Platform: {sys.platform} -- Python {platform.python_version()}, "
        f"pytask {_pytask.__version__}, pluggy {pluggy.__version__}"
    )
    click.echo(f"Root: {session.config['root'].as_posix()}")
    if session.config["config"] is not None:
        click.echo(f"Configuration: {session.config['config'].as_posix()}")

    plugin_info = session.config["pm"].list_plugin_distinfo()
    if plugin_info:
        formatted_plugins_w_versions = ", ".join(
            _format_plugin_names_and_versions(plugin_info)
        )
        click.echo(f"Plugins: {formatted_plugins_w_versions}")


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
    infos: List[Tuple[Any]], duration: float, color: str, terminal_width: int
) -> str:
    """Format the footer of the log message.

    Example
    -------
    >>> pytask_log_session_footer(
    ...     [(1, "succeeded", "green"), (1, "failed", "red")], 1, "red", 40
    ... )
    ===== 1 succeeded, 1 failed in 1s ======

    """
    message = _style_infos(infos)
    message += click.style(f" in {duration}s", fg=color)
    message = _wrap_string_ignoring_ansi_colors(f" {message} ", color, terminal_width)

    click.echo(message)


def _style_infos(infos: List[Tuple[Any]]) -> str:
    """Style infos.

    Example
    -------
    >>> m = _style_infos([(1, "a", "green"), (2, "b", "red"), (0, "c", "yellow")])
    >>> print(m)
    \x1b[32m1 a\x1b[0m, \x1b[31m2 b\x1b[0m

    """
    message = []
    for value, description, color in infos:
        if value:
            message.append(click.style(f"{value} {description}", fg=color))
    return ", ".join(message)


def _wrap_string_ignoring_ansi_colors(message: str, color: str, width: int):
    """Wrap a string with ANSI colors.

    This wrapper ignores the color codes which will increase the length of the string,
    but will not show up in the printed string.

    """
    n_characters = width - len(click.unstyle(message))
    n_left, n_right = math.floor(n_characters / 2), math.ceil(n_characters / 2)

    return (
        click.style("=" * n_left, fg=color)
        + message
        + click.style("=" * n_right, fg=color)
    )
