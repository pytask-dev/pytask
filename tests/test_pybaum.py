"""This module contains tests for pybaum and flexible dependencies and products."""
from __future__ import annotations

import textwrap

import pytest
from pybaum import tree_map
from pytask import main


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "decorator_name, exit_code", [("depends_on", 4), ("produces", 1)]
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

    products = tree_map(lambda x: x.value, getattr(session.tasks[0], decorator_name))
    expected = {
        0: tmp_path / "out.txt",
        1: {0: tmp_path / "tuple_out.txt"},
        2: {0: tmp_path / "list_out.txt"},
        3: {"a": tmp_path / "dict_out.txt", "b": {"c": tmp_path / "dict_out_2.txt"}},
    }
    assert products == expected
