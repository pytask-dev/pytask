import pytest
from _pytask.shared import convert_truthy_or_falsy_to_bool


@pytest.mark.parametrize(
    "value, expected",
    [
        (True, True),
        ("True", True),
        ("true", True),
        ("1", True),
        (False, False),
        ("False", False),
        ("false", False),
        ("0", False),
        (None, None),
    ],
)
def test_convert_truthy_or_falsy_to_bool(value, expected):
    result = convert_truthy_or_falsy_to_bool(value)
    assert result == expected


@pytest.mark.parametrize(
    "value, expectation",
    [(2, pytest.raises(ValueError)), (-1, pytest.raises(ValueError))],
)
def test_raise_error_convert_truthy_or_falsy_to_bool(value, expectation):
    with expectation:
        convert_truthy_or_falsy_to_bool(value)
