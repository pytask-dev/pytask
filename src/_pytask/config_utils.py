"""This module contains helper functions for the configuration."""
from __future__ import annotations

from enum import Enum
from typing import Callable


def parse_click_choice(
    name: str, enum_: type[Enum]
) -> Callable[[Enum | str | None], Enum | None]:
    """Validate the passed options for a :class:`click.Choice` option."""

    def _parse(x: Enum | str | None) -> Enum | None:
        members = list(enum_.__members__)
        if x in [None, "None", "none"]:
            out = None
        elif isinstance(x, str) and x in members:
            out = enum_[x]
        else:
            raise ValueError(f"'{name}' can only be one of {members}.")
        return out

    return _parse
