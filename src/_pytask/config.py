"""Configure pytask."""
from __future__ import annotations

import configparser
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any

import pluggy
import tomli
import tomli_w
from _pytask.config_utils import get_config_reader
from _pytask.console import console
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from _pytask.shared import parse_paths
from _pytask.shared import parse_value_or_multiline_option
from _pytask.shared import to_list
from rich.syntax import Syntax
from rich.text import Text


hookimpl = pluggy.HookimplMarker("pytask")


_IGNORED_FOLDERS: list[str] = [".git/*", ".hg/*", ".svn/*", ".venv/*"]


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


_DEPRECATION_MESSAGE = """WARNING: pytask.ini, tox.ini, and setup.cfg will be \
deprecated as configuration files for pytask starting with v0.3 or v1.0.

To upgrade and silence this warning, copy the content below in a pyproject.toml in the \
same directory as your old configuration file. This would be the path: {}. The content \
is equivalent to your current configuration.

Even if your configuration just has the header and no values, copy it. pytask needs \
the header to determine the root of your project.
"""


@hookimpl
def pytask_configure(
    pm: pluggy.PluginManager, config_from_cli: dict[str, Any]
) -> dict[str, Any]:
    """Configure pytask."""
    config = {"pm": pm}

    # Either the path to the configuration is passed via the CLI or it needs to be
    # detected from the paths passed to pytask.
    if config_from_cli.get("config"):
        config["config"] = Path(config_from_cli["config"])
        config["root"] = config["config"].parent
    else:
        paths = (
            parse_paths(config_from_cli.get("paths"))
            if config_from_cli.get("paths") is not None
            else [Path.cwd()]
        )
        config["root"], config["config"] = _find_project_root_and_config(paths)

    if config["config"] is None:
        config_from_file = {}
    else:
        read_config = get_config_reader(config["config"])
        config_from_file = read_config(config["config"])

        if read_config.__name__ == "_read_ini_config":
            toml_string = "# Content of pyproject.toml\n\n" + tomli_w.dumps(
                {"tool": {"pytask": {"ini_options": config_from_file}}}
            )
            console.print(
                Text(
                    _DEPRECATION_MESSAGE.format(
                        config["config"].with_name("pyproject.toml")
                    ),
                    style="warning",
                )
            )
            console.print(Syntax(toml_string, "toml"))

    # If paths are set in the configuration, process them.
    if config_from_file.get("paths"):
        paths_from_file = to_list(
            parse_value_or_multiline_option(config_from_file.get("paths"))
        )
        config_from_file["paths"] = [
            config["config"].parent.joinpath(p).resolve() for p in paths_from_file
        ]

    config["paths"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="paths",
        default=[Path.cwd()],
        callback=parse_paths,
    )

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
        config_from_file=config_from_file,
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
    config["command"] = config_from_cli.get("command", "build")

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

    config_from_file["task_files"] = parse_value_or_multiline_option(
        config_from_file.get("task_files")
    )
    config["task_files"] = to_list(
        get_first_non_none_value(
            config_from_file, key="task_files", default="task_*.py"
        )
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
            callback=lambda x: x if x is None else int(x),
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


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Sort markers alphabetically."""
    config["markers"] = {k: config["markers"][k] for k in sorted(config["markers"])}


def _find_project_root_and_config(paths: list[Path]) -> tuple[Path, Path]:
    """Find the project root and configuration file from a list of paths.

    The process is as follows:

    1. Find the common base directory of all paths passed to pytask (default to the
       current working directory).
    2. Starting from this directory, look at all parent directories, and return the file
       if it is found.
    3. If a directory contains a ``.git`` directory/file, a ``.hg`` directory, or the
       pyproject.toml file, stop searching.

    """
    try:
        common_ancestor = Path(os.path.commonpath(paths))
    except ValueError:
        warnings.warn(
            "A common path for all passed path could not be detected. Fall back to "
            "current working directory."
        )
        common_ancestor = Path.cwd()
    if common_ancestor.is_file():
        common_ancestor = common_ancestor.parent

    config_path = None
    root = None
    parent_directories = [common_ancestor] + list(common_ancestor.parents)

    for parent in parent_directories:
        for config_name in ["pyproject.toml", "pytask.ini", "tox.ini", "setup.cfg"]:

            path = parent.joinpath(config_name)

            if path.exists():
                try:
                    read_config = get_config_reader(path)
                    read_config(path)
                except configparser.Error as e:
                    raise configparser.Error(f"Could not read {path}.") from e
                except tomli.TOMLDecodeError as e:
                    raise tomli.TOMLDecodeError(f"Could not read {path}.") from e
                except KeyError:
                    pass
                else:
                    config_path = path
                    root = config_path.parent
                    break

        # If you hit a the top of a repository, stop searching further.
        if parent.joinpath(".git").exists():
            root = parent
            break

        if parent.joinpath(".hg").is_dir():
            root = parent
            break

    if root is None:
        root = common_ancestor

    return root, config_path
