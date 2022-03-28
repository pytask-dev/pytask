from __future__ import annotations

import re
from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from _pytask.config_utils import parse_click_choice
from _pytask.config_utils import ShowCapture


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expected, expectation",
    [
        (None, None, does_not_raise()),
        ("None", None, does_not_raise()),
        ("none", None, does_not_raise()),
        ("no", ShowCapture.NO, does_not_raise()),
        ("stdout", ShowCapture.STDOUT, does_not_raise()),
        ("stderr", ShowCapture.STDERR, does_not_raise()),
        ("all", ShowCapture.ALL, does_not_raise()),
        (
            "asd",
            None,
            pytest.raises(
                ValueError,
                match=re.escape(
                    "'show_capture' can only be one of ['no', 'stdout', 'stderr', "
                    "'all']."
                ),
            ),
        ),
        (
            1,
            None,
            pytest.raises(
                ValueError,
                match=re.escape(
                    "'show_capture' can only be one of ['no', 'stdout', 'stderr', "
                    "'all']."
                ),
            ),
        ),
    ],
)
def test_capture_callback(value, expected, expectation):
    with expectation:
        result = parse_click_choice("show_capture", ShowCapture)(value)
        assert result == expected
