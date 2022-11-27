"""This module contains helper functions for the configuration."""
from __future__ import annotations

import os
import warnings
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Callable

import click
import tomli
from _pytask.shared import parse_paths


def set_defaults_from_config(
    context: click.Context, param: click.Parameter, value: Any  # noqa: U100
) -> Path | None:
    """Set the defaults for the command-line interface from the configuration."""
    if value:
        context.params["config"] = value
        context.params["root"] = context.params["config"].parent
    else:
        if context.params["paths"] is None:
            context.params["paths"] = (Path.cwd(),)

        context.params["paths"] = parse_paths(context.params["paths"])
        (
            context.params["root"],
            context.params["config"],
        ) = _find_project_root_and_config(context.params["paths"])

    if context.params["config"] is None:
        return None

    config_from_file = read_config(context.params["config"])

    if context.default_map is None:
        context.default_map = {}

    context.default_map.update(config_from_file)

    return context.params["config"]


def _find_project_root_and_config(paths: list[Path]) -> tuple[Path, Path]:
    """Find the project root and configuration file from a list of paths.

    The process is as follows:

    1. Find the common base directory of all paths passed to pytask (default to the
       current working directory).
    2. Starting from this directory, look at all parent directories, and return the file
       if it is found.
    3. If a directory contains a ``.git`` directory/file, or the ``pyproject.toml``
       file, stop searching.

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
        path = parent.joinpath("pyproject.toml")

        if path.exists():
            try:
                read_config(path)
            except (tomli.TOMLDecodeError, OSError) as e:
                raise click.FileError(
                    filename=str(path), hint=f"Error reading {path}:\n{e}"
                ) from None
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

    if root is None:
        root = common_ancestor

    return root, config_path


def parse_click_choice(
    name: str, enum_: type[Enum]
) -> Callable[[Enum | str | None], Enum | None]:
    """Validate the passed options for a :class:`click.Choice` option."""
    value_to_name = {enum_[name].value: name for name in enum_.__members__}

    def _parse(x: Enum | str | None) -> Enum | None:
        if x in (None, "None", "none"):
            out = None
        elif isinstance(x, str) and x in value_to_name:
            out = enum_[value_to_name[x]]
        else:
            raise ValueError(f"'{name}' can only be one of {list(value_to_name)}.")
        return out

    return _parse


class ShowCapture(str, Enum):
    NO = "no"
    STDOUT = "stdout"
    STDERR = "stderr"
    ALL = "all"


def read_config(
    path: Path, sections: str = "tool.pytask.ini_options"
) -> dict[str, Any]:
    """Read the configuration from a ``*.toml`` file.

    Raises
    ------
    tomli.TOMLDecodeError
        Raised if ``*.toml`` could not be read.
    KeyError
        Raised if the specified sections do not exist.

    """
    sections_ = sections.split(".")

    config = tomli.loads(path.read_text(encoding="utf-8"))

    for section in sections_:
        config = config[section]

    return config
