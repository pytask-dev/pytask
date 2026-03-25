from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import TypeGuard
from typing import cast

if TYPE_CHECKING:
    from typing import Protocol

    from coiled.function import Function


__all__ = ["extract_coiled_function_kwargs", "is_coiled_function"]


if TYPE_CHECKING:

    class _CoiledFunctionPrivateAttrs(Protocol):
        _cluster_kwargs: dict[str, Any]
        _environ: dict[str, Any] | None
        _local: bool
        _name: str
        keepalive: Any | None


def is_coiled_function(obj: Any) -> TypeGuard[Function]:
    """Check whether an object is coiled's function wrapper."""
    cls = type(obj)
    return cls.__module__ == "coiled.function" and cls.__qualname__ == "Function"


def _as_coiled_private_attrs(func: Function) -> _CoiledFunctionPrivateAttrs:
    """Cast to the private-attribute layout used by coiled's Function class."""
    return cast("_CoiledFunctionPrivateAttrs", func)


def extract_coiled_function_kwargs(func: Function) -> dict[str, Any]:
    """Extract the kwargs for a coiled function."""
    coiled_function = _as_coiled_private_attrs(func)
    return {
        "cluster_kwargs": coiled_function._cluster_kwargs,
        "keepalive": coiled_function.keepalive,
        "environ": coiled_function._environ,
        "local": coiled_function._local,
        "name": coiled_function._name,
    }
