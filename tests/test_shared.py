from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import find_duplicates
from _pytask.shared import parse_value_or_multiline_option


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expectation, expected",
    [
        (True, does_not_raise(), True),
        ("True", does_not_raise(), True),
        ("true", does_not_raise(), True),
        ("1", does_not_raise(), True),
        (False, does_not_raise(), False),
        ("False", does_not_raise(), False),
        ("false", does_not_raise(), False),
        ("0", does_not_raise(), False),
        (None, does_not_raise(), None),
        ("None", does_not_raise(), None),
        ("none", does_not_raise(), None),
        ("asklds", pytest.raises(ValueError, match="Input"), None),
    ],
)
def test_convert_truthy_or_falsy_to_bool(value, expectation, expected):
    with expectation:
        result = convert_truthy_or_falsy_to_bool(value)
        assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expectation",
    [(2, pytest.raises(ValueError)), (-1, pytest.raises(ValueError))],
)
def test_raise_error_convert_truthy_or_falsy_to_bool(value, expectation):
    with expectation:
        convert_truthy_or_falsy_to_bool(value)


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expectation, expected",
    [
        (None, does_not_raise(), None),
        ("None", does_not_raise(), None),
        ("none", does_not_raise(), None),
        ("first\nsecond", does_not_raise(), ["first", "second"]),
        ("first", does_not_raise(), "first"),
        ("", does_not_raise(), None),
        (1, pytest.raises(ValueError, match="Input 1"), None),
    ],
)
def test_parse_value_or_multiline_option(value, expectation, expected):
    with expectation:
        result = parse_value_or_multiline_option(value)
        assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "x, expected",
    [([], set()), ([1, 2, 3, 1, 2], {1, 2}), (["a", "a", "b"], {"a"})],
)
def test_find_duplicates(x, expected):
    result = find_duplicates(x)
    assert result == expected
