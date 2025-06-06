from __future__ import annotations

import pytest

import pytask


@pytest.mark.parametrize(
    ("lhs", "rhs", "expected"),
    [
        (pytask.mark.foo(), pytask.mark.foo(), True),
        (pytask.mark.foo(), pytask.mark.bar(), False),
        (pytask.mark.foo(), "bar", False),
        ("foo", pytask.mark.bar(), False),
    ],
)
def test__eq__(lhs, rhs, expected) -> None:
    assert (lhs == rhs) == expected


@pytest.mark.filterwarnings("ignore:Unknown pytask\\.mark\\.foo")
def test_aliases() -> None:
    md = pytask.mark.foo(1, "2", three=3)
    assert md.name == "foo"
    assert md.args == (1, "2")
    assert md.kwargs == {"three": 3}
