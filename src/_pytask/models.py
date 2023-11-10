"""Contains code on models, containers and there like."""
from __future__ import annotations

from typing import Any
from typing import Callable
from typing import NamedTuple
from typing import TYPE_CHECKING

from attrs import define
from attrs import field

if TYPE_CHECKING:
    from pathlib import Path
    from _pytask.tree_util import PyTree
    from _pytask.mark import Mark


@define
class CollectionMetadata:
    """A class for carrying metadata from functions to tasks."""

    id_: str | None = None
    """The id for a single parametrization."""
    is_ready: Callable[..., bool] | None = None
    """A callable that indicates whether a delayed task is ready."""
    kwargs: dict[str, Any] = field(factory=dict)
    """Contains kwargs which are necessary for the task function on execution."""
    markers: list[Mark] = field(factory=list)
    """Contains the markers of the function."""
    name: str | None = None
    """The name of the task function."""
    produces: PyTree[Any] | None = None
    """Definition of products to handle returns."""


class NodeInfo(NamedTuple):
    arg_name: str
    path: tuple[str | int, ...]
    task_path: Path | None
    task_name: str
    value: Any


class DelayedTask(NamedTuple):
    path: Path | None
    name: str
    obj: Any
