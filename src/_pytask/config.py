"""Configure pytask."""
import configparser
import itertools
import os
import shutil
import warnings
from pathlib import Path
from typing import List

import click
import pluggy
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from _pytask.shared import parse_paths
from _pytask.shared import parse_value_or_multiline_option
from _pytask.shared import to_list


hookimpl = pluggy.HookimplMarker("pytask")


IGNORED_FOLDERS = [
    ".git/*",
    ".hg/*",
    ".svn/*",
    ".venv/*",
    "*.egg-info/*",
    ".ipynb_checkpoints/*",
    ".mypy_cache/*",
    ".nox/*",
    ".tox/*",
    "_build/*",
    "__pycache__/*",
    "build/*",
    "dist/*",
]
"""List[str]: List of expressions to ignore folders."""


@hookimpl
def pytask_configure(pm, config_from_cli):
    """Configure pytask."""
    config = {"pm": pm, "terminal_width": _get_terminal_width()}

    # Either the path to the configuration is passed via the CLI or it needs to be
    # detected from the paths passed to pytask.
    if config_from_cli.get("config"):
        config["config"] = Path.cwd().joinpath(config_from_cli["config"])
        config["root"] = config["config"].parent
    else:
        paths = (
            parse_paths(config_from_cli.get("paths"))
            if config_from_cli.get("paths") is not None
            else [Path.cwd()]
        )
        config["root"], config["config"] = _find_project_root_and_ini(paths)

    config_from_file = (
        _read_config(config["config"]) if config["config"] is not None else {}
    )

    # If paths are set in the configuration, process them.
    if config_from_file.get("paths"):
        paths_from_file = parse_value_or_multiline_option(config_from_file.get("paths"))
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
        "depends_on": "Attach a dependency/dependencies to a task.",
        "produces": "Attach a product/products to a task.",
    }

    pm.hook.pytask_parse_config(
        config=config,
        config_from_cli=config_from_cli,
        config_from_file=config_from_file,
    )

    pm.hook.pytask_post_parse(config=config)

    return config


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    """Parse the configuration."""
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
        + IGNORED_FOLDERS
    )

    config["debug_pytask"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="debug_pytask",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    if config["debug_pytask"]:
        config["pm"].trace.root.setwriter(click.echo)
        config["pm"].enable_tracing()

    config_from_file["task_files"] = parse_value_or_multiline_option(
        config_from_file.get("task_files")
    )
    config["task_files"] = to_list(
        get_first_non_none_value(
            config_from_file, key="task_files", default="task_*.py"
        )
    )


@hookimpl
def pytask_post_parse(config):
    """Sort markers alphabetically."""
    config["markers"] = {k: config["markers"][k] for k in sorted(config["markers"])}


def _find_project_root_and_ini(paths: List[Path]):
    """Find the project root and configuration file from a list of paths."""
    try:
        common_ancestor = Path(os.path.commonpath(paths))
    except ValueError:
        warnings.warn(
            "A common path for all passed path could not be detected. Fall back to "
            "current working directory."
        )
        common_ancestor = Path.cwd()

    config_path = None
    parent_directories = (
        common_ancestor.parents
        if common_ancestor.is_file()
        else [common_ancestor] + list(common_ancestor.parents)
    )
    for parent, config_name in itertools.product(
        parent_directories, ["pytask.ini", "tox.ini", "setup.cfg"]
    ):
        path = parent.joinpath(config_name)

        if path.exists():
            try:
                _read_config(path)
            except Exception:
                pass
            else:
                config_path = path
                break

    if config_path is not None:
        root = config_path.parent
    else:
        root = common_ancestor if common_ancestor.is_dir() else common_ancestor.parent

    return root, config_path


def _read_config(path):
    """Read the configuration from a file with a [pytask] section."""
    config = configparser.ConfigParser()
    config.read(path)
    return dict(config["pytask"])


def _get_terminal_width() -> int:
    """Get the window width of the terminal."""
    width, _ = shutil.get_terminal_size(fallback=(80, 24))

    # The Windows get_terminal_size may be bogus, let's sanitize a bit.
    if width < 40:
        width = 80

    # Delete one character which prevents accidental line breaks.
    width -= 1

    return width
