"""Contains the plugin manager."""
from __future__ import annotations

import pluggy
from _pytask import hookspecs


def get_plugin_manager() -> pluggy.PluginManager:
    """Get the plugin manager."""
    pm = pluggy.PluginManager("pytask")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("pytask")

    return pm
