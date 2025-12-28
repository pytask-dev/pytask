"""Contains code for tree utilities."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar

import optree
from optree import tree_flatten_with_path as _optree_tree_flatten_with_path
from optree import tree_leaves as _optree_tree_leaves
from optree import tree_map as _optree_tree_map
from optree import tree_map_with_path as _optree_tree_map_with_path
from optree import tree_structure as _optree_tree_structure

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

if TYPE_CHECKING:
    # Use our own recursive type alias for static type checking.
    # optree's PyTree uses __class_getitem__ to generate Union types at runtime,
    # but type checkers like ty cannot evaluate these dynamic types properly.
    # See: https://github.com/metaopt/optree/issues/251
    PyTree = (
        _T | tuple["PyTree[_T]", ...] | list["PyTree[_T]"] | dict[Any, "PyTree[_T]"]
    )
else:
    from optree import PyTree

assert optree.__file__ is not None
TREE_UTIL_LIB_DIRECTORY = Path(optree.__file__).parent


tree_leaves = functools.partial(
    _optree_tree_leaves, none_is_leaf=True, namespace="pytask"
)
tree_map = functools.partial(_optree_tree_map, none_is_leaf=True, namespace="pytask")
tree_map_with_path = functools.partial(
    _optree_tree_map_with_path, none_is_leaf=True, namespace="pytask"
)
tree_structure = functools.partial(
    _optree_tree_structure, none_is_leaf=True, namespace="pytask"
)
tree_flatten_with_path = functools.partial(
    _optree_tree_flatten_with_path, none_is_leaf=True, namespace="pytask"
)
