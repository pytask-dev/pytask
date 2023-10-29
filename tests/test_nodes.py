from __future__ import annotations

from pathlib import Path

import pytest
from _pytask.nodes import PathNode
from _pytask.nodes import PythonNode
from _pytask.nodes import Task
from _pytask.nodes import TaskWithoutPath


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("value", "hash_", "expected"),
    [
        (0, False, "0"),
        (0, True, "0"),
        (0, lambda x: 1, "1"),  # noqa: ARG005
        ("0", False, "0"),
        ("0", True, "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"),
    ],
)
def test_hash_of_python_node(value, hash_, expected):
    node = PythonNode(name="test", value=value, hash=hash_)
    state = node.state()
    assert state == expected


@pytest.mark.parametrize(
    ("node", "expected"),
    [
        (
            PathNode(name="pathnode", path=Path("file.txt")),
            "7bc22c56319caa1f5abac40cd732395ef572d2376c84b443cbfada7ae164205e",
        ),
        (
            PythonNode(name="name", value=None),
            "c8265d64828f9e007a9108251883a2b63954c326c678fca23c49a0b08ea7c925",
        ),
        (
            Task(base_name="task", path=Path("task.py"), function=None),
            "4c96feb6042210c859938d4f6fc835ac1bde64960aeda101d2e2367644f9c22b",
        ),
        (
            TaskWithoutPath(name="task", function=None),
            "ac80b202671ece4c139a9b2d6e03a499c8b6e016dcd2022ac580fbf1c64fc63b",
        ),
    ],
)
def test_signature(node, expected):
    assert node.signature == expected
