"""Contains the plugin manager."""

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

from attrs import define
from pluggy import HookimplMarker
from pluggy import PluginManager

from _pytask import hookspecs

if TYPE_CHECKING:
    from collections.abc import Iterable

__all__ = [
    "get_plugin_manager",
    "hookimpl",
    "register_hook_impls_from_modules",
    "storage",
]


hookimpl = HookimplMarker("pytask")


def register_hook_impls_from_modules(
    plugin_manager: PluginManager, module_names: Iterable[str]
) -> None:
    """Register hook implementations from modules."""
    for module_name in module_names:
        module = importlib.import_module(module_name)
        plugin_manager.register(module)


@hookimpl
def pytask_add_hooks(pm: PluginManager) -> None:
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
        "_pytask.provisional",
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


def get_plugin_manager() -> PluginManager:
    """Get the plugin manager."""
    pm = PluginManager("pytask")
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints("pytask")

    pm.register(sys.modules[__name__])
    pm.hook.pytask_add_hooks.call_historic(kwargs={"pm": pm})

    return pm


@define
class _PluginManagerStorage:
    """A class to store the plugin manager.

    This storage is needed to harmonize the two different ways to call pytask, via the
    CLI or the API.

    When pytask is called from the CLI, the plugin manager is created in
    :mod:`_pytask.cli` outside the click command to extend the command line interface.
    Afterwards, it needs to be accessed in the different commands.

    When pytask is called from the API, the plugin manager needs to be created inside
    the function, for example, :func:`~pytask.build` to ensure each call can start from
    a blank slate and is able to register any plugins.

    """

    _plugin_manager: PluginManager | None = None

    def create(self) -> PluginManager:
        """Create the plugin manager."""
        self._plugin_manager = get_plugin_manager()
        return self._plugin_manager

    def get(self) -> PluginManager:
        """Get the plugin manager."""
        assert self._plugin_manager
        return self._plugin_manager

    def store(self, pm: PluginManager) -> None:
        """Store the plugin manager."""
        self._plugin_manager = pm


storage = _PluginManagerStorage()
