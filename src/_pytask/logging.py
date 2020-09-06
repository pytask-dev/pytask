"""Add general logging capabilities."""
import platform
import sys
from typing import List

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
    if session.config["ini"] is not None:
        click.echo(f"Configuration: {session.config['ini'].as_posix()}")

    plugin_info = session.config["pm"].list_plugin_distinfo()
    if plugin_info:
        formatted_plugins_w_versions = ", ".join(
            _format_plugin_names_and_versions(plugin_info)
        )
        click.echo(f"Plugins: {formatted_plugins_w_versions}")


def _format_plugin_names_and_versions(plugininfo) -> List[str]:
    """Format name and version of loaded plugins."""
    values = []  # type: List[str]
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
