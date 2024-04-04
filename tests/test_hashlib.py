from __future__ import annotations

from pathlib import Path

import pytest
from _pytask._hashlib import hash_value


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, 1),
        (1.0, 1),
        (
            "Hello, World!",
            "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
        ),
        (
            b"Hello, World!",
            "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f",
        ),
        (
            Path("file.py"),
            "48b38abeefb3ba2622b6d1534d36c1ffd9b4deebf2cd71e4af8a33723e734ada",
        ),
    ],
)
def test_hash_value(value, expected):
    hash_ = hash_value(value)
    assert hash_ == expected
