from __future__ import annotations

import functools
from enum import Enum
from typing import Any
from typing import Final
from typing import Literal
from typing import TypeAlias

from attr import define


__all__ = ["Product", "ProductType"]


@define(frozen=True)
class ProductType:
    """A class to mark products."""


Product = ProductType()
"""ProductType: A singleton to mark products in annotations."""


def is_task_function(func: Any) -> bool:
    return (callable(func) and hasattr(func, "__name__")) or (
        isinstance(func, functools.partial) and hasattr(func.func, "__name__")
    )


class _NoDefault(Enum):
    no_default = ...


no_default: Final = _NoDefault.no_default
NoDefault: TypeAlias = Literal[_NoDefault.no_default]
