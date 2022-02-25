from __future__ import annotations

from typing import Any

from attrs import define
from attrs import field


@define
class CollectionMetadata:
    kwargs: dict[str, Any] = field(factory=dict)
