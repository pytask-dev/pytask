from __future__ import annotations

import pickle

import pytest
from pytask import PathNode
from pytask import PickleNode
from pytask import PythonNode


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


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("value", "hash_", "expected"),
    [
        ("0", False, "0"),
        (
            "0",
            lambda x: 1,  # noqa: ARG005
            "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9",
        ),
        ("0", True, "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"),
    ],
)
def test_hash_of_path_node(tmp_path, value, hash_, expected):
    path = tmp_path.joinpath("text.txt")
    path.write_text(value)
    node = PathNode(name="test", path=path, hash=hash_)
    state = node.state()
    if hash_:
        assert state == expected
    else:
        assert isinstance(state, str)


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("value", "hash_", "expected"),
    [
        ("0", False, "0"),
        (0, True, "ac57d54dcc34f2ebf6f410f6d7fab436eb84f8f6b640782134b3d8062ebf71d0"),
        (
            "0",
            lambda x: 1,  # noqa: ARG005
            "2e81f502b7a28f824c4f1451c946b952eebe65a8521925ef8f6135ef6f422e8e",
        ),
        ("0", True, "2e81f502b7a28f824c4f1451c946b952eebe65a8521925ef8f6135ef6f422e8e"),
    ],
)
def test_hash_of_pickle_node(tmp_path, value, hash_, expected):
    path = tmp_path.joinpath("text.pkl")
    path.write_bytes(pickle.dumps(value))
    node = PickleNode(name="test", path=path, hash=hash_)
    state = node.state()
    if hash_:
        assert state == expected
    else:
        assert isinstance(state, str)
