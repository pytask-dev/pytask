from __future__ import annotations

from typing import Any
from typing import Callable

from attrs import define

try:
    from coiled.function import Function
except ImportError:

    @define
    class Function:  # type: ignore[no-redef]
        cluster_kwargs: dict[str, Any]
        environ: dict[str, Any]
        function: Callable[..., Any] | None
        keepalive: str | None


__all__ = ["Function"]


def extract_coiled_function_kwargs(func: Function) -> dict[str, Any]:
    """Extract the kwargs for a coiled function."""
    return {
        "cluster_kwargs": func._cluster_kwargs,
        "keepalive": func.keepalive,
        "environ": func._environ,
        "local": func._local,
        "name": func._name,
    }
