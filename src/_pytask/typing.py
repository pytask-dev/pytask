from __future__ import annotations

from attr import define


__all__ = ["Product", "ProductType"]


@define(frozen=True)
class ProductType:
    """A class to mark products."""


Product = ProductType()
"""ProductType: A singleton to mark products in annotations."""
