"""Contains code for tree utilities."""

from __future__ import annotations

import typing  # noqa: F401  # Needed to resolve optree.PyTree forward refs.
from collections.abc import Callable  # noqa: TC003  # Public annotations need it.
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import TypeAlias
from typing import TypeVar
from typing import cast
from typing import overload

import optree
from optree import PyTreeSpec

__all__ = [
    "TREE_UTIL_LIB_DIRECTORY",
    "PyTree",
    "tree_flatten_with_path",
    "tree_leaves",
    "tree_map",
    "tree_map_with_path",
    "tree_structure",
]

_T = TypeVar("_T")
_U = TypeVar("_U")
_K = TypeVar("_K")

if TYPE_CHECKING:
    # Use our own recursive type alias for static type checking.
    # optree's PyTree uses __class_getitem__ to generate Union types at runtime,
    # but type checkers like ty cannot evaluate these dynamic types properly.
    # See: https://github.com/metaopt/optree/issues/251
    PyTree: TypeAlias = (
        _T | tuple["PyTree[_T]", ...] | list["PyTree[_T]"] | dict[Any, "PyTree[_T]"]
    )
else:
    from optree import PyTree

assert optree.__file__ is not None
TREE_UTIL_LIB_DIRECTORY = Path(optree.__file__).parent

_pytree = optree.pytree.reexport(namespace="pytask")


def tree_leaves(
    tree: PyTree[_T],
    /,
    is_leaf: Callable[[Any], bool] | None = None,
) -> list[_T]:
    """Return the leaves of a pytask tree."""
    return cast(
        "list[_T]",
        _pytree.leaves(
            cast("Any", tree),
            is_leaf,
            none_is_leaf=True,
        ),
    )


@overload
def tree_map(
    func: Callable[..., PyTree[_T]],
    tree: dict[_K, PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> dict[_K, PyTree[_T]]: ...


@overload
def tree_map(
    func: Callable[..., _U],
    tree: dict[_K, PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> dict[_K, PyTree[_U]]: ...


@overload
def tree_map(
    func: Callable[..., PyTree[_T]],
    tree: list[PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> list[PyTree[_T]]: ...


@overload
def tree_map(
    func: Callable[..., _U],
    tree: list[PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> list[PyTree[_U]]: ...


@overload
def tree_map(
    func: Callable[..., PyTree[_T]],
    tree: tuple[PyTree[_T], ...],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> tuple[PyTree[_T], ...]: ...


@overload
def tree_map(
    func: Callable[..., _U],
    tree: tuple[PyTree[_T], ...],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> tuple[PyTree[_U], ...]: ...


@overload
def tree_map(
    func: Callable[..., _U],
    tree: PyTree[_T],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> PyTree[_U]: ...


def tree_map(
    func: Callable[..., Any],
    tree: PyTree[Any],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> Any:
    """Apply a function to each leaf of a pytask tree."""
    return _pytree.map(
        func,
        cast("Any", tree),
        *cast("tuple[Any, ...]", rests),
        is_leaf=is_leaf,
        none_is_leaf=True,
    )


@overload
def tree_map_with_path(
    func: Callable[..., PyTree[_T]],
    tree: dict[_K, PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> dict[_K, PyTree[_T]]: ...


@overload
def tree_map_with_path(
    func: Callable[..., _U],
    tree: dict[_K, PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> dict[_K, PyTree[_U]]: ...


@overload
def tree_map_with_path(
    func: Callable[..., PyTree[_T]],
    tree: list[PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> list[PyTree[_T]]: ...


@overload
def tree_map_with_path(
    func: Callable[..., _U],
    tree: list[PyTree[_T]],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> list[PyTree[_U]]: ...


@overload
def tree_map_with_path(
    func: Callable[..., PyTree[_T]],
    tree: tuple[PyTree[_T], ...],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> tuple[PyTree[_T], ...]: ...


@overload
def tree_map_with_path(
    func: Callable[..., _U],
    tree: tuple[PyTree[_T], ...],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> tuple[PyTree[_U], ...]: ...


@overload
def tree_map_with_path(
    func: Callable[..., _U],
    tree: PyTree[_T],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> PyTree[_U]: ...


def tree_map_with_path(
    func: Callable[..., Any],
    tree: PyTree[Any],
    /,
    *rests: PyTree[Any],
    is_leaf: Callable[[Any], bool] | None = None,
) -> Any:
    """Apply a function to each leaf and pass the leaf path."""
    return _pytree.map_with_path(
        func,
        cast("Any", tree),
        *cast("tuple[Any, ...]", rests),
        is_leaf=is_leaf,
        none_is_leaf=True,
    )


def tree_structure(
    tree: PyTree[Any],
    /,
    is_leaf: Callable[[Any], bool] | None = None,
) -> PyTreeSpec:
    """Return the tree structure of a pytask tree."""
    return _pytree.structure(cast("Any", tree), is_leaf, none_is_leaf=True)


def tree_flatten_with_path(
    tree: PyTree[_T],
    /,
    is_leaf: Callable[[Any], bool] | None = None,
) -> tuple[list[tuple[Any, ...]], list[_T], PyTreeSpec]:
    """Flatten a pytask tree into paths, leaves, and structure."""
    return cast(
        "tuple[list[tuple[Any, ...]], list[_T], PyTreeSpec]",
        _pytree.flatten_with_path(
            cast("Any", tree),
            is_leaf,
            none_is_leaf=True,
        ),
    )
