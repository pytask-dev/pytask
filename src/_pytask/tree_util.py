"""Contains code for tree utilities."""
from __future__ import annotations

import functools
from pathlib import Path

import optree
from optree import PyTree
from optree import tree_leaves as _optree_tree_leaves
from optree import tree_map as _optree_tree_map
from optree import tree_map_with_path as _optree_tree_map_with_path


__all__ = [
    "tree_leaves",
    "tree_map",
    "tree_map_with_path",
    "PyTree",
    "TREE_UTIL_LIB_DIRECTORY",
]

TREE_UTIL_LIB_DIRECTORY = Path(optree.__file__).parent


tree_leaves = functools.partial(
    _optree_tree_leaves, none_is_leaf=True, namespace="pytask"
)
tree_map = functools.partial(_optree_tree_map, none_is_leaf=True, namespace="pytask")
tree_map_with_path = functools.partial(
    _optree_tree_map_with_path, none_is_leaf=True, namespace="pytask"
)
