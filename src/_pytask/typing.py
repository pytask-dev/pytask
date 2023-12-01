from __future__ import annotations

import functools
import inspect
from enum import Enum
from typing import Any
from typing import Final
from typing import Literal
from typing import TYPE_CHECKING

from _pytask.node_protocols import PTask
from attrs import define

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


__all__ = [
    "NoDefault",
    "Product",
    "ProductType",
    "is_task_function",
    "no_default",
    "pretends_to_be_a_task",
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


def pretends_to_be_a_task(obj: Any) -> bool:
    """Check if an object is really a :class:`~pytask.PTask`.

    Some object are overwriting ``__getattr__`` and therefore any ``isinstance`` check
    with our protocols will invetibly return ``True``.

    This check goes one step further and checks whether the attributes have conforming
    types.

    See :issue:`507` for the initial bug report.

    """
    if not isinstance(obj, PTask):
        return False

    # Catches Task or TaskWithoutPath imported in a module.
    if not inspect.isclass(obj):
        return True

    # Catches, for example, ``from ibis import _``, objects that overwrote
    # ``__getattr__``.
    if not isinstance(obj.markers, list):
        return True
    return False


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
