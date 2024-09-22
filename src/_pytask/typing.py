from __future__ import annotations

import functools
from enum import Enum
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import Literal

from attrs import define

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from pytask import PTask


__all__ = [
    "NoDefault",
    "Product",
    "ProductType",
    "is_task_function",
    "no_default",
]


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


def is_task_generator(task: PTask) -> bool:
    """Check if a task is a generator."""
    return task.attributes.get("is_generator", False)


class _NoDefault(Enum):
    """A singleton for no defaults.

    We make this an Enum
    1) because it round-trips through pickle correctly (see GH#40397)
    2) because mypy does not understand singletons

    """

    no_default = "NO_DEFAULT"

    def __repr__(self) -> str:
        return "<no_default>"


no_default: Final = _NoDefault.no_default
"""The value for missing defaults."""
NoDefault: TypeAlias = Literal[_NoDefault.no_default]
"""The type annotation."""
