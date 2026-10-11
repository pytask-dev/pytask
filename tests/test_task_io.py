"""Tests for task-specific operations on recursive node trees."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from _pytask.nodes import DirectoryNode
from _pytask.nodes import PythonNode
from pytask.task_io import concrete_product_nodes
from pytask.task_io import map_task_io
from pytask.task_io import task_node_leaves

if TYPE_CHECKING:
    from _pytask.node_protocols import TaskIO


def test_task_io_preserves_nested_nodes_and_paths() -> None:
    first = PythonNode(name="first")
    second = PythonNode(name="second")
    products: TaskIO = {"return": [first, {"nested": (second,)}]}

    assert task_node_leaves(products) == [first, second]
    assert task_node_leaves(products["return"]) == [first, second]
    assert concrete_product_nodes(products) == [first, second]
    assert map_task_io(lambda path, node: (path, node.name), products) == {
        "return": [
            (("return", 0), "first"),
            {"nested": ((("return", 1, "nested", 0), "second"),)},
        ]
    }


def test_concrete_products_reject_uncollected_provisional_node() -> None:
    products: TaskIO = {"return": [DirectoryNode()]}

    with pytest.raises(TypeError, match="Uncollected provisional product"):
        concrete_product_nodes(products)
