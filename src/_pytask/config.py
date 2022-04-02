"""Configure pytask."""
from __future__ import annotations

import configparser
import itertools
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any

import pluggy
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from _pytask.shared import parse_paths
from _pytask.shared import parse_value_or_multiline_option
from _pytask.shared import to_list


hookimpl = pluggy.HookimplMarker("pytask")


_IGNORED_FOLDERS: list[str] = [
    ".git/*",
    ".hg/*",
    ".svn/*",
    ".venv/*",
]


_IGNORED_FILES: list[str] = [
    ".codecov.yml",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".pytask.sqlite3",
    ".readthedocs.yml",
    ".readthedocs.yaml",
    "readthedocs.yml",
    "readthedocs.yaml",
    "environment.yml",
    "pyproject.toml",
    "pytask.ini",
    "setup.cfg",
    "tox.ini",
]


_IGNORED_FILES_AND_FOLDERS: list[str] = _IGNORED_FILES + _IGNORED_FOLDERS


IGNORED_TEMPORARY_FILES_AND_FOLDERS: list[str] = [
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
]


def is_file_system_case_sensitive() -> bool:
    """Check whether the file system is case-sensitive."""
    with tempfile.NamedTemporaryFile(prefix="TmP") as tmp_file:
        return not os.path.exists(tmp_file.name.lower())


IS_FILE_SYSTEM_CASE_SENSITIVE = is_file_system_case_sensitive()


@hookimpl
def pytask_configure(
    pm: pluggy.PluginManager, config: dict[str, Any]
) -> dict[str, Any]:
    """Configure pytask."""
    config.attrs["pm"] = pm

    all_paths = config.get_all("paths")
    config.attrs["paths"] = next(
        parse_paths(value, Path.cwd()) for value in all_paths if value is not None
    )

    if config.get("config") is not None:
        config.attrs["root"] = config.get("config").parent
    else:
        config.attrs["root"] = _find_project_root(config.get("paths"))

    config.attrs["markers"] = {
        "depends_on": "Attach a dependency/dependencies to a task.",
        "produces": "Attach a product/products to a task.",
        "try_first": "Try to execute a task a early as possible.",
        "try_last": "Try to execute a task a late as possible.",
    }

    pm.hook.pytask_parse_config(config=config)

    config.consolidate()

    pm.hook.pytask_post_parse(config=config)

    return config


@hookimpl(trylast=True)
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    if config.get("stop_after_first_failure"):
        config.attrs["max_failures"] = 1

    all_ignores = [i for i in config.get_all("ignore") if i is not None]
    config.attrs["ignore"] = (
        all_ignores + _IGNORED_FILES_AND_FOLDERS + IGNORED_TEMPORARY_FILES_AND_FOLDERS
    )


@hookimpl
def pytask_post_parse(config):
    if config.option.debug_pytask:
        config.option.pm.trace.root.setwriter(print)  # noqa: T002
        config.option.pm.enable_tracing()


def _find_project_root(paths: list[Path]) -> Path:
    """Find the project root and configuration file from a list of paths."""
    try:
        common_ancestor = Path(os.path.commonpath(paths))
    except ValueError:
        warnings.warn(
            "A common path for all passed path could not be detected. Fall back to "
            "current working directory."
        )
        common_ancestor = Path.cwd()

    root = common_ancestor if common_ancestor.is_dir() else common_ancestor.parent

    return root


def _read_config(path: Path) -> dict[str, Any]:
    """Read the configuration from a file with a [pytask] section."""
    config = configparser.ConfigParser()
    config.read(path)
    return dict(config["pytask"])
