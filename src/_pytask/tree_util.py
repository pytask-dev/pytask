"""Contains code for tree utilities."""
from __future__ import annotations

from pathlib import Path

import optree
from optree import PyTree
from optree import tree_leaves as tree_just_flatten
from optree import tree_leaves as tree_just_yield
from optree import tree_map
from optree import tree_map_with_path


__all__ = [
    "tree_just_flatten",
    "tree_map",
    "tree_map_with_path",
    "tree_just_yield",
    "PyTree",
    "TREE_UTIL_LIB_DIRECTORY",
]

TREE_UTIL_LIB_DIRECTORY = Path(optree.__file__).parent
