from __future__ import annotations

import functools
from typing import Any

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
