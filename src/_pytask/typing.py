from __future__ import annotations

from enum import Enum
from typing import Literal

from attr import define


__all__ = ["no_value", "NoValue"]


class _NoValue(Enum):
    """Sentinel value when no value was provided.

    For nodes, we need a different default value than :obj:`None` to signal that the
    user provided no value.

    We make this an Enum

    - because it round-trips through pickle correctly (see GH#pandas/40397)
    - because mypy does not understand singletons

    """

    no_value = "NO_VALUE"

    def __repr__(self) -> str:
        return "<no_value>"


# Note: no_value is exported to the public API in pytask
no_value = _NoValue.no_value
NoValue = Literal[_NoValue.no_value]


@define(frozen=True)
class ProductType:
    """A class to mark products."""


Product = ProductType()
"""ProductType: A singleton to mark products in annotations."""
