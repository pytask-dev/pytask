"""This module contains code on models, containers and there like."""
from __future__ import annotations

from typing import Any

import attr


@attr.s
class CollectionMetadata:
    """A class for carrying metadata from functions to tasks."""

    kwargs = attr.ib(factory=dict, type=dict[str, Any])
