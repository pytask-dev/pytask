"""Configure pytask."""
from __future__ import annotations

import os
import tempfile
from typing import Any

import pluggy
from _pytask.shared import parse_paths
from _pytask.shared import to_list


hookimpl = pluggy.HookimplMarker("pytask")


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
        return not os.path.exists(tmp_file.name.lower())


IS_FILE_SYSTEM_CASE_SENSITIVE = is_file_system_case_sensitive()


@hookimpl
def pytask_configure(
    pm: pluggy.PluginManager, config_from_cli: dict[str, Any]
) -> dict[str, Any]:
    """Configure pytask."""
    config = {"pm": pm, **config_from_cli}

    config["markers"] = {
        "depends_on": (
            "Add dependencies to a task. See this tutorial for more information: "
            "[link https://bit.ly/3JlxylS]https://bit.ly/3JlxylS[/]."
        ),
        "produces": (
            "Add products to a task. See this tutorial for more information: "
            "[link https://bit.ly/3JlxylS]https://bit.ly/3JlxylS[/]."
        ),
        "try_first": "Try to execute a task a early as possible.",
        "try_last": "Try to execute a task a late as possible.",
    }

    pm.hook.pytask_parse_config(
        config=config,
        config_from_cli=config_from_cli,
        config_from_file={},
    )

    pm.hook.pytask_post_parse(config=config)

    return config


@hookimpl
def pytask_parse_config(
    config: dict[str, Any], config_from_cli: dict[str, Any]
) -> None:
    """Parse the configuration."""
    config["paths"] = parse_paths(config_from_cli["paths"])

    config["ignore"] = (
        to_list(config_from_cli["ignore"])
        + _IGNORED_FILES_AND_FOLDERS
        + IGNORED_TEMPORARY_FILES_AND_FOLDERS
    )

    config["task_files"] = config_from_cli.get("task_files", "task_*.py")

    if config["stop_after_first_failure"]:
        config["max_failures"] = 1
    else:
        config["max_failures"] = config_from_cli["max_failures"]

    for name in ("check_casing_of_paths",):
        config[name] = bool(config_from_cli.get(name, True))

    for name in ("debug_pytask", "dry_run", "stop_after_first_failure", "verbose"):
        config[name] = config_from_cli[name]

    if config["debug_pytask"]:
        config["pm"].trace.root.setwriter(print)  # noqa: T202
        config["pm"].enable_tracing()


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Sort markers alphabetically."""
    config["markers"] = {k: config["markers"][k] for k in sorted(config["markers"])}
