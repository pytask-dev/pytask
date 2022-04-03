"""This module contains helper functions for the configuration."""
from __future__ import annotations

import configparser
import fnmatch
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Callable

import tomli


def parse_click_choice(
    name: str, enum_: type[Enum]
) -> Callable[[Enum | str | None], Enum | None]:
    """Validate the passed options for a :class:`click.Choice` option."""
    value_to_name = {enum_[name].value: name for name in enum_.__members__}

    def _parse(x: Enum | str | None) -> Enum | None:
        if x in [None, "None", "none"]:
            out = None
        elif isinstance(x, str) and x in value_to_name:
            out = enum_[value_to_name[x]]
        else:
            raise ValueError(f"'{name}' can only be one of {list(value_to_name)}.")
        return out

    return _parse


class ShowCapture(Enum):
    NO = "no"
    STDOUT = "stdout"
    STDERR = "stderr"
    ALL = "all"


def _read_ini_config(path: Path, sections: str = "pytask") -> dict[str, Any]:
    """Read the configuration from a ``*.ini`` file.

    Raises
    ------
    configparser.Error
        Raised if ``*.ini`` could not be read.
    KeyError
        Raised if the specified sections do not exist.

    """
    sections_ = sections.split(".")

    config = configparser.ConfigParser()
    config.read(path, encoding="utf-8")

    config_ = dict(config)
    for section in sections_:
        config_ = dict(config_[section])  # type: ignore

    return config_


def _read_toml_config(
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


def get_config_reader(path: Path) -> Callable[[Path], dict[str, Any]]:
    """Get a loader for a config file."""
    loaders = {
        "*.ini": _read_ini_config,
        "*.cfg": _read_ini_config,
        "*.toml": _read_toml_config,
    }

    for pattern, loader in loaders.items():
        matches = fnmatch.fnmatch(path.as_posix(), pattern)

        if matches:
            return loader
    else:
        return _read_ini_config
