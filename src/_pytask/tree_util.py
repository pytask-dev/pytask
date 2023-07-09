"""Contains code for tree utilities."""
from __future__ import annotations

from pathlib import Path

import optree
from optree import tree_leaves as tree_just_flatten
from optree import tree_leaves as tree_just_yield
from optree import tree_map


__all__ = [
    "tree_just_flatten",
    "tree_map",
    "tree_just_yield",
    "TREE_UTIL_LIB_DIRECTORY",
]

TREE_UTIL_LIB_DIRECTORY = Path(optree.__file__).parent
