from __future__ import annotations

import os
from pathlib import Path

import pytest
import upath

from _pytask._hashlib import hash_value


class RemotePathLike(os.PathLike[str]):
    def __init__(self, value: str) -> None:
        self.value = value

    def __fspath__(self) -> str:
        return self.value


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
        (
            RemotePathLike("s3://bucket/file.pkl"),
            "5bbedd1ab74242143481060b901083e77080661d97003b96e0cbae3a887ebce6",
        ),
    ],
)
def test_hash_value(value, expected):
    hash_ = hash_value(value)
    assert hash_ == expected


def test_hash_value_of_remote_upath():
    hash_ = hash_value(upath.UPath("s3://bucket/file.pkl"))

    assert hash_ == "5bbedd1ab74242143481060b901083e77080661d97003b96e0cbae3a887ebce6"
