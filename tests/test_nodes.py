from __future__ import annotations

import pickle
from pathlib import Path

import pytest
from pytask import PathNode
from pytask import PickleNode
from pytask import PNode
from pytask import PPathNode
from pytask import PythonNode
from pytask import Task
from pytask import TaskWithoutPath


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
            "66e5d35cb2f9f892935ed00fb2a639172c9078ce81e0e9e3bdab19d2f212ef50",
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


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("value", "exists", "expected"),
    [
        ("0", False, None),
        ("0", True, "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"),
    ],
)
def test_hash_of_path_node(tmp_path, value, exists, expected):
    path = tmp_path.joinpath("text.txt")
    if exists:
        path.write_text(value)
    node = PathNode(name="test", path=path)
    state = node.state()
    if exists:
        assert state == expected
    else:
        assert state is expected


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("value", "exists", "expected"),
    [
        ("0", False, None),
        ("0", True, "2e81f502b7a28f824c4f1451c946b952eebe65a8521925ef8f6135ef6f422e8e"),
    ],
)
def test_hash_of_pickle_node(tmp_path, value, exists, expected):
    path = tmp_path.joinpath("text.pkl")
    if exists:
        path.write_bytes(pickle.dumps(value))
    node = PickleNode(name="test", path=path)
    state = node.state()
    if exists:
        assert state == expected
    else:
        assert state is expected


@pytest.mark.parametrize(
    ("node", "protocol", "expected"),
    [
        (PathNode, PNode, True),
        (PathNode, PPathNode, True),
        (PythonNode, PNode, True),
        (PythonNode, PPathNode, False),
        (PickleNode, PNode, True),
        (PickleNode, PPathNode, True),
    ],
)
def test_comply_with_protocol(node, protocol, expected):
    assert isinstance(node, protocol) is expected
