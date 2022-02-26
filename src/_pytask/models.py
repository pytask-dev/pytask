"""This module contains code on models, containers and there like."""
from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import TYPE_CHECKING

import attr

if TYPE_CHECKING:
    from _pytask.mark import Mark


@attr.s
class CollectionMetadata:
    """A class for carrying metadata from functions to tasks."""

    kwargs = attr.ib(factory=dict, type=Dict[str, Any])
    """Contains kwargs which are necessary for the task function on execution."""
    markers = attr.ib(factory=list, type=List["Mark"])
    """Contains the markers of the function."""
