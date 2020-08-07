import platform
import sys
from typing import List

import click
import pluggy
import pytask
from _pytask.config import hookimpl


@hookimpl
def pytask_log_session_header(session):
    tm_width = session.config["terminal_width"]

    click.echo(f"{{:=^{tm_width}}}".format(" Start pytask session "), nl=True)
    click.echo(
        f"Platform: {sys.platform} -- Python {platform.python_version()}, "
        f"pytask {pytask.__version__}, pluggy {pluggy.__version__}"
    )
    click.echo(f"Root: {session.config['root'].as_posix()}")
    if session.config["ini"] is not None:
        click.echo(f"Configuration: {session.config['ini'].as_posix()}")

    plugin_info = session.config["pm"].list_plugin_distinfo()
    if plugin_info:
        formatted_plugins_w_versions = ", ".join(_plugin_nameversions(plugin_info))
        click.echo(f"Plugins: {formatted_plugins_w_versions}")


def _plugin_nameversions(plugininfo) -> List[str]:
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
