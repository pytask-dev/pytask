"""Contains code on models, containers and there like."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import NamedTuple
from uuid import UUID
from uuid import uuid4

from attrs import define
from attrs import field

if TYPE_CHECKING:
    from pathlib import Path

    from _pytask.mark import Mark
    from _pytask.tree_util import PyTree


@define
class CollectionMetadata:
    """A class for carrying metadata from functions to tasks.

    Attributes
    ----------
    after
        An expression or a task function or a list of task functions that need to be
        executed before this task can.
    id_
        An id for the task if it is part of a parametrization. Otherwise, an automatic
        id will be generated. See
        :doc:`this tutorial <../tutorials/repeating_tasks_with_different_inputs>` for
        more information.
    is_generator
        An indicator for whether a task generates other tasks or not.
    kwargs
        A dictionary containing keyword arguments which are passed to the task when it
        is executed.
    markers
        A list of markers that are attached to the task.
    name
        Use it to override the name of the task that is, by default, the name of the
        callable.
    produces
        Definition of products to parse the function returns and store them. See
        :doc:`this how-to guide <../how_to_guides/using_task_returns>` for more
        information.
    """

    after: str | list[Callable[..., Any]] = field(factory=list)
    attributes: dict[str, Any] = field(factory=dict)
    is_generator: bool = False
    id_: str | None = None
    kwargs: dict[str, Any] = field(factory=dict)
    markers: list[Mark] = field(factory=list)
    name: str | None = None
    produces: PyTree[Any] | None = None
    _id: UUID = field(factory=uuid4)


class NodeInfo(NamedTuple):
    arg_name: str
    path: tuple[str | int, ...]
    task_path: Path | None
    task_name: str
    value: Any
