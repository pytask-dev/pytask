from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from attrs import define

if TYPE_CHECKING:
    from collections.abc import Callable

try:
    from coiled.function import Function
except ImportError:

    @define
    class Function:
        cluster_kwargs: dict[str, Any]
        environ: dict[str, Any]
        function: Callable[..., Any] | None
        keepalive: str | None


__all__ = ["Function"]


def extract_coiled_function_kwargs(func: Function) -> dict[str, Any]:
    """Extract the kwargs for a coiled function."""
    return {
        "cluster_kwargs": func._cluster_kwargs,  # ty: ignore[possibly-missing-attribute]
        "keepalive": func.keepalive,
        "environ": func._environ,  # ty: ignore[possibly-missing-attribute]
        "local": func._local,  # ty: ignore[possibly-missing-attribute]
        "name": func._name,  # ty: ignore[possibly-missing-attribute]
    }
