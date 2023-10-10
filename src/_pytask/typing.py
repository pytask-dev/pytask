from __future__ import annotations

import functools
from enum import Enum
from typing import Any
from typing import Final
from typing import Literal
from typing import TYPE_CHECKING

from attrs import define

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


__all__ = ["Product", "ProductType"]


@define(frozen=True)
class ProductType:
    """A class to mark products."""


Product = ProductType()
"""ProductType: A singleton to mark products in annotations."""


def is_task_function(obj: Any) -> bool:
    """Check if an object is a task function."""
    return (callable(obj) and hasattr(obj, "__name__")) or (
        isinstance(obj, functools.partial) and hasattr(obj.func, "__name__")
    )


class _NoDefault(Enum):
    """An enum for missing defaults."""

    no_default = ...


no_default: Final = _NoDefault.no_default
"""The value for missing defaults."""
NoDefault: TypeAlias = Literal[_NoDefault.no_default]
"""The type annotation."""
