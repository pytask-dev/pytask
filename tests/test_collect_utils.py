from __future__ import annotations

from typing import Annotated

from _pytask.collect_utils import _find_args_with_product_annotation
from pytask import Product


def test_find_args_with_product_annotation():
    def func(
        a: Annotated[int, Product], b: float, c, d: Annotated[int, float]
    ):  # pragma: no cover
        return a, b, c, d

    result = _find_args_with_product_annotation(func)
    assert result == ["a"]
