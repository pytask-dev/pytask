"""Configure pytask."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from _pytask.pluginmanager import hookimpl
from _pytask.shared import parse_paths
from _pytask.shared import to_list

if TYPE_CHECKING:
    from pluggy import PluginManager

    from _pytask.settings import Settings


_IGNORED_FOLDERS: list[str] = [".git/*", ".venv/*"]


_IGNORED_FILES: list[str] = [
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
    config["root"].joinpath(".pytask").mkdir(exist_ok=True, parents=True)

    config["paths"] = parse_paths(config["paths"])

    config["markers"] = {
        "try_first": "Try to execute a task a early as possible.",
        "try_last": "Try to execute a task a late as possible.",
        **config["markers"],
    }

    config["ignore"] = (
        to_list(config["ignore"])
        + _IGNORED_FILES_AND_FOLDERS
        + IGNORED_TEMPORARY_FILES_AND_FOLDERS
    )

    value = config.get("task_files", ["task_*.py"])
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(p, str) for p in value
    ):
        msg = "'task_files' must be a list of patterns."
        raise ValueError(msg)
    config["task_files"] = value

    if config["stop_after_first_failure"]:
        config["max_failures"] = 1

    for name in ("check_casing_of_paths",):
        config[name] = bool(config.get(name, True))

    if config["debug_pytask"]:
        config["pm"].trace.root.setwriter(print)
        config["pm"].enable_tracing()


@hookimpl
def pytask_post_parse(config: Settings) -> None:
    """Sort markers alphabetically."""
    config["markers"] = {k: config["markers"][k] for k in sorted(config["markers"])}
