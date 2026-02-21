from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from collections.abc import Callable

try:
    from coiled.function import Function
except ImportError:

    @dataclass
    class Function:
        cluster_kwargs: dict[str, Any]
        environ: dict[str, Any]
        function: Callable[..., Any] | None
        keepalive: str | None


__all__ = ["Function"]


_MISSING = object()


def _get_coiled_attribute(func: Function, *names: str, default: Any = _MISSING) -> Any:
    """Get an attribute from coiled function objects with private/public fallbacks."""
    for name in names:
        value = getattr(func, name, _MISSING)
        if value is not _MISSING:
            return value
    if default is not _MISSING:
        return default
    names_as_text = ", ".join(repr(name) for name in names)
    msg = f"Cannot find coiled attribute(s) {names_as_text} on {func!r}."
    raise AttributeError(msg)


def extract_coiled_function_kwargs(func: Function) -> dict[str, Any]:
    """Extract the kwargs for a coiled function."""
    return {
        "cluster_kwargs": _get_coiled_attribute(
            func, "_cluster_kwargs", "cluster_kwargs"
        ),
        "keepalive": func.keepalive,
        "environ": _get_coiled_attribute(func, "_environ", "environ"),
        "local": _get_coiled_attribute(func, "_local", "local", default=None),
        "name": _get_coiled_attribute(func, "_name", "name", default=None),
    }
