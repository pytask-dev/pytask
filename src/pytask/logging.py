import platform
import sys

import click
import pluggy
import pytask
from _pytest.terminal import _plugin_nameversions


@pytask.hookimpl
def pytask_log_session_header(session):
    tm_width = session.config["terminal_width"]

    click.echo(f"{{:=^{tm_width}}}".format(" Start pytask session "), nl=True)
    click.echo(
        f"Platform: {sys.platform} -- Python {platform.python_version()}, "
        f"pytask {pytask.__version__}, pluggy {pluggy.__version__}"
    )
    click.echo(f"Root: {session.config['root'].as_posix()}")

    plugin_info = session.config["pm"].list_plugin_distinfo()
    if plugin_info:
        formatted_plugins_w_versions = ", ".join(_plugin_nameversions(plugin_info))
        click.echo(f"Plugins: {formatted_plugins_w_versions}")
