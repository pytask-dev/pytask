from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import attr
import pytask
import pytest
from _pytask.collect import _extract_nodes_from_function_markers
from _pytask.nodes import depends_on
from _pytask.nodes import produces
from _pytask.shared import reduce_node_name
from pytask import FilePathNode
from pytask import MetaNode


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "values, expected", [("a", ["a"]), (["b"], [["b"]]), (["e", "f"], [["e", "f"]])]
)
def test_extract_args_from_mark(decorator, values, expected):
    @decorator(values)
    def task_example():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(_extract_nodes_from_function_markers(task_example, parser))
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "values, expected",
    [
        ({"objects": "a"}, ["a"]),
        ({"objects": ["b"]}, [["b"]]),
        ({"objects": ["e", "f"]}, [["e", "f"]]),
    ],
)
def test_extract_kwargs_from_mark(decorator, values, expected):
    @decorator(**values)
    def task_example():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(_extract_nodes_from_function_markers(task_example, parser))
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "args, kwargs", [(["a", "b"], {"objects": "a"}), (("a"), {"objects": "a"})]
)
def test_raise_error_for_invalid_args_to_depends_on_and_produces(
    decorator, args, kwargs
):
    @decorator(*args, **kwargs)
    def task_example():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    with pytest.raises(TypeError):
        list(_extract_nodes_from_function_markers(task_example, parser))


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


@attr.s
class FalseNode:
    path = attr.ib()


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
