"""Configure pytask."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from _pytask.pluginmanager import hookimpl
from _pytask.shared import parse_paths

if TYPE_CHECKING:
    from pluggy import PluginManager

    from _pytask.settings import Settings


_IGNORED_FOLDERS: tuple[str, ...] = (".git/*", ".venv/*")
_IGNORED_FILES: tuple[str, ...] = (
    ".codecov.yml",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".readthedocs.yml",
    ".readthedocs.yaml",
    "readthedocs.yml",
    "readthedocs.yaml",
    "environment.yml",
    "pyproject.toml",
    "setup.cfg",
    "tox.ini",
)
_IGNORED_FILES_AND_FOLDERS: tuple[str, ...] = _IGNORED_FILES + _IGNORED_FOLDERS
IGNORED_TEMPORARY_FILES_AND_FOLDERS: tuple[str, ...] = (
    "*.egg-info/*",
    ".ipynb_checkpoints/*",
    ".mypy_cache/*",
    ".nox/*",
    ".tox/*",
    "_build/*",
    "__pycache__/*",
    "build/*",
    "dist/*",
    "pytest_cache/*",
)


def is_file_system_case_sensitive() -> bool:
    """Check whether the file system is case-sensitive."""
    with tempfile.NamedTemporaryFile(prefix="TmP") as tmp_file:
        return not Path(tmp_file.name.lower()).exists()


IS_FILE_SYSTEM_CASE_SENSITIVE = is_file_system_case_sensitive()


@hookimpl
def pytask_configure(pm: PluginManager, config: Settings) -> Settings:
    """Configure pytask."""
    pm.hook.pytask_parse_config(config=config)
    pm.hook.pytask_post_parse(config=config)
    return config


@hookimpl
def pytask_parse_config(config: Settings) -> None:
    """Parse the configuration."""
    config.common.cache.mkdir(exist_ok=True, parents=True)

    config.common.paths = parse_paths(config.common.paths)

    config.markers.markers = {
        "try_first": "Try to execute a task a early as possible.",
        "try_last": "Try to execute a task a late as possible.",
        **config.markers.markers,
    }

    config.common.ignore = (
        config.common.ignore
        + _IGNORED_FILES_AND_FOLDERS
        + IGNORED_TEMPORARY_FILES_AND_FOLDERS
    )

    if config.build.stop_after_first_failure:
        config.build.max_failures = 1

    if config.common.debug_pytask:
        config.common.pm.trace.root.setwriter(print)
        config.common.pm.enable_tracing()


@hookimpl
def pytask_post_parse(config: Settings) -> None:
    """Sort markers alphabetically."""
    config.markers.markers = {
        k: config.markers.markers[k] for k in sorted(config.markers.markers)
    }
