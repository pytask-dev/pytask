from __future__ import annotations

import pytest
from _pytask.shared import find_duplicates


@pytest.mark.unit
@pytest.mark.parametrize(
    "x, expected",
    [([], set()), ([1, 2, 3, 1, 2], {1, 2}), (["a", "a", "b"], {"a"})],
)
def test_find_duplicates(x, expected):
    result = find_duplicates(x)
    assert result == expected
