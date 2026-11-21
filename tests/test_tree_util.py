"""Contains tests for tree_util and flexible dependencies and products."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass

import optree
import pytest

from pytask import ExitCode
from pytask import build
from pytask import cli
from pytask.tree_util import tree_flatten_with_path
from pytask.tree_util import tree_leaves
from pytask.tree_util import tree_map
from pytask.tree_util import tree_map_with_path
from pytask.tree_util import tree_structure


@dataclass(frozen=True)
class _Box:
    value: object


@pytest.mark.parametrize(
    ("helper", "reference", "args"),
    [
        (tree_flatten_with_path, optree.tree_flatten_with_path, ()),
        (tree_leaves, optree.tree_leaves, ()),
        (tree_map, optree.tree_map, (str,)),
        (
            tree_map_with_path,
            optree.tree_map_with_path,
            (lambda path, value: (path, value),),
        ),
        (tree_structure, optree.tree_structure, ()),
    ],
)
@pytest.mark.parametrize("namespace", ["pytask", "pytask-test-custom"])
@pytest.mark.parametrize("none_is_leaf", [True, False])
def test_tree_helper_traversal_keywords(
    helper, reference, args, namespace, none_is_leaf
):
    optree.register_pytree_node(
        _Box,
        lambda box: ((box.value,), None),
        lambda _metadata, children: _Box(children[0]),
        namespace=namespace,
    )
    try:
        tree = [_Box(1), None]
        options = {}
        if namespace != "pytask":
            options["namespace"] = namespace
        if not none_is_leaf:
            options["none_is_leaf"] = False
        expected = reference(
            *args, tree, none_is_leaf=none_is_leaf, namespace=namespace
        )
        assert helper(*args, tree, **options) == expected
    finally:
        optree.unregister_pytree_node(_Box, namespace=namespace)


@pytest.mark.parametrize("arg_name", ["depends_on", "produces"])
def test_task_with_complex_product_did_not_produce_node(tmp_path, arg_name):
    source = f"""
    from pathlib import Path

    complex = [
        Path("out.txt"),
        (Path("tuple_out.txt"),),
        [Path("list_out.txt")],
        {{"a": Path("dict_out.txt"), "b": {{"c": Path("dict_out_2.txt")}}}},
    ]

    def task_example({arg_name}=complex):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.FAILED

    products = tree_map(lambda x: x.load(), getattr(session.tasks[0], arg_name))
    expected = [
        tmp_path / "out.txt",
        (tmp_path / "tuple_out.txt",),
        [tmp_path / "list_out.txt"],
        {"a": tmp_path / "dict_out.txt", "b": {"c": tmp_path / "dict_out_2.txt"}},
    ]
    expected = {arg_name: expected}
    assert products == expected


def test_profile_with_pytree(tmp_path, runner):
    source = """
    from pytask.tree_util import tree_leaves
    from pathlib import Path

    def task_example(
        produces=[{"out_1": Path("out_1.txt")}, {"out_2": Path("out_2.txt")}]
    ):
        for p in tree_leaves(produces):
            p.write_text("There are nine billion bicycles in Beijing.")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task." in result.output
    assert "Duration (in s)" in result.output
    assert "0." in result.output
    assert "Size of Products" in result.output
    assert "86 bytes" in result.output


@pytest.mark.parametrize(
    ("prefix_tree", "full_tree", "strict", "expected"),
    [
        # This is why strict cannot be true when parsing function returns.
        (1, 1, True, False),
        (1, 1, False, True),
        ({"a": 1, "b": 1}, {"a": 1, "b": {"c": 1, "d": 1}}, False, True),
        ({"a": 1, "b": 1}, {"a": 1, "b": {"c": 1, "d": 1}}, True, True),
    ],
)
def test_is_prefix(prefix_tree, full_tree, strict, expected):
    prefix_structure = tree_structure(prefix_tree)
    full_tree_structure = tree_structure(full_tree)
    assert prefix_structure.is_prefix(full_tree_structure, strict=strict) is expected
