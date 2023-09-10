from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.nodes import PythonNode
from _pytask.shared import reduce_node_name
from pytask import PathNode


_ROOT = Path.cwd()


@pytest.mark.integration()
@pytest.mark.parametrize(
    ("node", "paths", "expectation", "expected"),
    [
        pytest.param(
            PathNode.from_path(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("alternative_src")],
            does_not_raise(),
            "pytask/src/module.py",
            id="Common path found for PathNode not in 'paths' and 'paths'",
        ),
        pytest.param(
            PathNode.from_path(_ROOT.joinpath("top/src/module.py")),
            [_ROOT.joinpath("top/src")],
            does_not_raise(),
            "src/module.py",
            id="make filepathnode relative to 'paths'.",
        ),
    ],
)
def test_reduce_node_name(node, paths, expectation, expected):
    with expectation:
        result = reduce_node_name(node, paths)
        assert result == expected


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
