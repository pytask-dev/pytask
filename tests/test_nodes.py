from __future__ import annotations

import pytest
from _pytask.nodes import PythonNode


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
