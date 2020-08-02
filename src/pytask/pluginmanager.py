import click
import pluggy
from pytask import hookspecs


def get_plugin_manager():
    pm = pluggy.PluginManager("pytask")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("pytask")

    return pm


def activate_tracing_for_pluggy(pm):
    pm.trace.root.setwriter(click.echo)
    pm.enable_tracing()
