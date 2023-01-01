from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.shared import reduce_node_name
from attrs import define
from pytask import FilePathNode
from pytask import MetaNode


@pytest.mark.unit
def test_instantiation_of_metanode():
    class Node(MetaNode):
        ...

    with pytest.raises(TypeError):
        Node()

    class Node(MetaNode):
        def state(self):
            ...

    task = Node()
    assert isinstance(task, MetaNode)


@define
class FalseNode:
    path: Path


_ROOT = Path.cwd()


@pytest.mark.integration
@pytest.mark.parametrize(
    "node, paths, expectation, expected",
    [
        pytest.param(
            FilePathNode.from_path(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("alternative_src")],
            does_not_raise(),
            "pytask/src/module.py",
            id="Common path found for FilePathNode not in 'paths' and 'paths'",
        ),
        pytest.param(
            FalseNode(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("src")],
            pytest.raises(TypeError, match="Unknown node"),
            None,
            id="throw error on unknown node type.",
        ),
        pytest.param(
            FilePathNode.from_path(_ROOT.joinpath("top/src/module.py")),
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
