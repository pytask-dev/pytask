"""Configure pytask."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from _pytask.console import console
from _pytask.pluginmanager import hookimpl
from _pytask.shared import parse_markers
from _pytask.shared import parse_paths
from _pytask.shared import to_list

if TYPE_CHECKING:
    from pluggy import PluginManager


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
def pytask_configure(pm: PluginManager, raw_config: dict[str, Any]) -> dict[str, Any]:
    """Configure pytask."""
    # Add all values by default so that many plugins do not need to copy over values.
    config = {"pm": pm, "markers": {}} | raw_config
    config["markers"] = parse_markers(config["markers"])  # type: ignore[arg-type]

    pm.hook.pytask_parse_config(config=config)
    pm.hook.pytask_post_parse(config=config)

    return config


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    config["root"].joinpath(".pytask").mkdir(exist_ok=True, parents=True)

    # Ensure a .gitignore file exists in the .pytask directory to avoid accidentally
    # committing the cache.
    gitignore_path = config["root"].joinpath(".pytask", ".gitignore")
    if not gitignore_path.exists():
        gitignore_path.write_text("# Automatically added by pytask.\n*\n")

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
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Sort markers alphabetically."""
    config["markers"] = {k: config["markers"][k] for k in sorted(config["markers"])}

    # Show a warning to the user if they passed a path pointing to a Python module that
    # does not match the task file pattern.
    for path in config["paths"]:
        if path.is_file() and not any(
            path.match(pattern) for pattern in config["task_files"]
        ):
            msg = (
                f"Warning: The path '{path}' does not match any of the task file "
                f"patterns in {config['task_files']}. Rename the file or configure a "
                "different 'task_files' pattern if you want to collect it."
            )
            console.print(msg, style="warning")
