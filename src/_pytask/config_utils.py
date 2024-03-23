"""Contains helper functions for the configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from typing import Sequence

import click

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib


__all__ = ["find_project_root_and_config", "read_config"]


def consolidate_settings_and_arguments(settings: Any, arguments: dict[str, Any]) -> Any:
    """Consolidate the settings and the values from click arguments.

    Values from the command line have precedence over the settings from the
    configuration file or from environment variables. Thus, we just plug in the values
    from the command line into the settings.

    """
    for key, value in arguments.items():
        # We do not want to overwrite the settings with None or empty tuples that come
        # from ``multiple=True`` The default is handled by the settings class.
        if value is not None and value != ():
            setattr(settings, key, value)
    return settings


def find_project_root_and_config(
    paths: Sequence[Path] | None,
) -> tuple[Path, Path | None]:
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
        common_ancestor = Path(os.path.commonpath(paths))  # type: ignore[arg-type]
    except ValueError:
        common_ancestor = Path.cwd()

    if common_ancestor.is_file():
        common_ancestor = common_ancestor.parent

    config_path = None
    root = None
    parent_directories = [common_ancestor, *list(common_ancestor.parents)]

    for parent in parent_directories:
        path = parent.joinpath("pyproject.toml")

        if path.exists():
            try:
                read_config(path)
            except (tomllib.TOMLDecodeError, OSError) as e:  # pragma: no cover
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


def read_config(
    path: Path, sections: str = "tool.pytask.ini_options"
) -> dict[str, Any]:
    """Read the configuration from a ``*.toml`` file.

    Raises
    ------
    tomllib.TOMLDecodeError
        Raised if ``*.toml`` could not be read.
    KeyError
        Raised if the specified sections do not exist.

    """
    sections_ = sections.split(".")

    config = tomllib.loads(path.read_text(encoding="utf-8"))

    for section in sections_:
        config = config[section]

    # Only convert paths when possible. Otherwise, we defer the error until the click
    # takes over.
    if (
        "paths" in config
        and isinstance(config["paths"], list)
        and all(isinstance(p, str) for p in config["paths"])
    ):
        config["paths"] = [path.parent.joinpath(p).resolve() for p in config["paths"]]

    return config
