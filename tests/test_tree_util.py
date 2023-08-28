"""This module contains tests for tree_util and flexible dependencies and products."""
from __future__ import annotations

import textwrap

import pytest
from _pytask.outcomes import ExitCode
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_structure
from pytask import cli
from pytask import main


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("decorator_name", "exit_code"),
    [
        ("depends_on", ExitCode.DAG_FAILED),
        ("produces", ExitCode.FAILED),
    ],
)
def test_task_with_complex_product_did_not_produce_node(
    tmp_path, decorator_name, exit_code
):
    source = f"""
    import pytask


    complex = [
        "out.txt",
        ("tuple_out.txt",),
        ["list_out.txt"],
        {{"a": "dict_out.txt", "b": {{"c": "dict_out_2.txt"}}}},
    ]


    @pytask.mark.{decorator_name}(complex)
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == exit_code

    products = tree_map(lambda x: x.load(), getattr(session.tasks[0], decorator_name))
    expected = {
        0: tmp_path / "out.txt",
        1: {0: tmp_path / "tuple_out.txt"},
        2: {0: tmp_path / "list_out.txt"},
        3: {"a": tmp_path / "dict_out.txt", "b": {"c": tmp_path / "dict_out_2.txt"}},
    }
    expected = {decorator_name: expected}
    assert products == expected


@pytest.mark.end_to_end()
def test_profile_with_pytree(tmp_path, runner):
    source = """
    import time
    import pytask
    from _pytask.tree_util import tree_leaves

    @pytask.mark.produces([{"out_1": "out_1.txt"}, {"out_2": "out_2.txt"}])
    def task_example(produces):
        time.sleep(2)
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


@pytest.mark.unit()
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
