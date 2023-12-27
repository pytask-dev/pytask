"""Contains the plugin manager."""
from __future__ import annotations

import importlib
import sys
from typing import Iterable

import pluggy
from _pytask import hookspecs
from pluggy import HookimplMarker
from pluggy import PluginManager


hookimpl = HookimplMarker("pytask")


def register_hook_impls_from_modules(
    plugin_manager: PluginManager, module_names: Iterable[str]
) -> None:
    """Register hook implementations from modules."""
    for module_name in module_names:
        module = importlib.import_module(module_name)
        plugin_manager.register(module)


@hookimpl
def pytask_add_hooks(pm: pluggy.PluginManager) -> None:
    """Add hooks."""
    builtin_hook_impl_modules = (
        "_pytask.build",
        "_pytask.capture",
        "_pytask.clean",
        "_pytask.collect",
        "_pytask.collect_command",
        "_pytask.config",
        "_pytask.dag",
        "_pytask.dag_command",
        "_pytask.database",
        "_pytask.debugging",
        "_pytask.execute",
        "_pytask.live",
        "_pytask.logging",
        "_pytask.mark",
        "_pytask.nodes",
        "_pytask.parameters",
        "_pytask.persist",
        "_pytask.profile",
        "_pytask.skipping",
        "_pytask.task",
        "_pytask.warnings",
    )
    register_hook_impls_from_modules(pm, builtin_hook_impl_modules)


def get_plugin_manager() -> pluggy.PluginManager:
    """Get the plugin manager."""
    pm = pluggy.PluginManager("pytask")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("pytask")

    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks.call_historic(kwargs={"pm": pm})

    return pm
