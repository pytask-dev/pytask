from __future__ import annotations

import pytest
from _pytask.parametrize_utils import arg_value_to_id_component


@pytest.mark.unit
@pytest.mark.parametrize(
    "arg_name, arg_value, i, id_func, expected",
    [
        ("arg", 1, 0, None, "1"),
        ("arg", True, 0, None, "True"),
        ("arg", False, 0, None, "False"),
        ("arg", 1.0, 0, None, "1.0"),
        ("arg", None, 0, None, "arg0"),
        ("arg", (1,), 0, None, "arg0"),
        ("arg", [1], 0, None, "arg0"),
        ("arg", {1, 2}, 0, None, "arg0"),
        ("arg", 1, 0, bool, "True"),
        ("arg", 1, 1, lambda x: None, "1"),
        ("arg", [1], 2, lambda x: None, "arg2"),
    ],
)
def test_arg_value_to_id_component(arg_name, arg_value, i, id_func, expected):
    result = arg_value_to_id_component(arg_name, arg_value, i, id_func)
    assert result == expected
