"""Configure pytask."""
from __future__ import annotations

import os
import tempfile
from typing import Any

import pluggy
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from _pytask.shared import parse_paths
from _pytask.shared import parse_value_or_multiline_option
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
    config: dict[str, Any],
    config_from_cli: dict[str, Any],
    config_from_file: dict[str, Any],
) -> None:
    """Parse the configuration."""
    # TODO: Do I need it?
    config["command"] = config_from_cli.get("command", "build")

    config["paths"] = parse_paths(config_from_cli["paths"])

    config_from_file["ignore"] = parse_value_or_multiline_option(
        config_from_file.get("ignore")
    )
    config["ignore"] = (
        to_list(
            get_first_non_none_value(
                config_from_cli,
                config_from_file,
                key="ignore",
                default=[],
            )
        )
        + _IGNORED_FILES_AND_FOLDERS
        + IGNORED_TEMPORARY_FILES_AND_FOLDERS
    )

    config["debug_pytask"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="debug_pytask",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    if config["debug_pytask"]:
        config["pm"].trace.root.setwriter(print)  # noqa: T202
        config["pm"].enable_tracing()

    config["task_files"] = to_list(
        get_first_non_none_value(config_from_cli, key="task_files", default="task_*.py")
    )

    config["stop_after_first_failure"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="stop_after_first_failure",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    if config["stop_after_first_failure"]:
        config["max_failures"] = 1
    else:
        config["max_failures"] = get_first_non_none_value(
            config_from_cli,
            config_from_file,
            key="max_failures",
            default=float("inf"),
            callback=lambda x: x if x is None or x == float("inf") else int(x),
        )

    config["check_casing_of_paths"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="check_casing_of_paths",
        default=True,
        callback=convert_truthy_or_falsy_to_bool,
    )

    config["verbose"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="verbose",
        default=1,
        callback=lambda x: x if x is None else int(x),
    )

    config["sort_table"] = convert_truthy_or_falsy_to_bool(
        config_from_file.get("sort_table", True)
    )

    config["dry_run"] = config_from_cli.get("dry_run", False)


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Sort markers alphabetically."""
    config["markers"] = {k: config["markers"][k] for k in sorted(config["markers"])}
