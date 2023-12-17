from __future__ import annotations

import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from _pytask.outcomes import ExitCode
from _pytask.shared import convert_to_enum
from _pytask.shared import find_duplicates
from pytask import build
from pytask import ShowCapture


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("x", "expected"),
    [([], set()), ([1, 2, 3, 1, 2], {1, 2}), (["a", "a", "b"], {"a"})],
)
def test_find_duplicates(x, expected):
    result = find_duplicates(x)
    assert result == expected


@pytest.mark.end_to_end()
def test_parse_markers(tmp_path):
    toml = """
    [tool.pytask.ini_options.markers]
    a1 = "this is a webtest marker"
    a2 = "this is a smoke marker"
    """
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(toml))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert "a1" in session.config["markers"]
    assert "a2" in session.config["markers"]


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("value", "enum", "expectation", "expected"),
    [
        ("all", ShowCapture, does_not_raise(), ShowCapture.ALL),
        ("a", ShowCapture, pytest.raises(ValueError, match="Value 'a' is not "), None),
    ],
)
def test_convert_to_enum(value, enum, expectation, expected):
    with expectation:
        result = convert_to_enum(value, enum)
        assert result == expected
