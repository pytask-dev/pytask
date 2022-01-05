"""This module contains everything related to reports."""
from types import TracebackType
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

import attr
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info


if TYPE_CHECKING:
    from _pytask.nodes import MetaNode
    from _pytask.nodes import MetaTask


ExceptionInfo = Tuple[Type[BaseException], BaseException, Union[TracebackType, None]]


@attr.s
class CollectionReport:
    """A collection report for a task."""

    outcome = attr.ib(type=CollectionOutcome)
    node = attr.ib(default=None, type="MetaNode")
    exc_info = attr.ib(default=None, type=ExceptionInfo)

    @classmethod
    def from_node(
        cls, outcome: CollectionOutcome, node: "MetaNode"
    ) -> "CollectionReport":
        return cls(outcome=outcome, node=node)

    @classmethod
    def from_exception(
        cls: Type["CollectionReport"],
        outcome: CollectionOutcome,
        exc_info: ExceptionInfo,
        node: Optional["MetaNode"] = None,
    ) -> "CollectionReport":
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(outcome=outcome, node=node, exc_info=exc_info)


@attr.s
class ResolvingDependenciesReport:
    """A report for an error while resolving dependencies."""

    exc_info = attr.ib(type=ExceptionInfo)

    @classmethod
    def from_exception(cls, exc_info: ExceptionInfo) -> "ResolvingDependenciesReport":
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(exc_info)


@attr.s
class ExecutionReport:
    """A report for an executed task."""

    task = attr.ib(type="MetaTask")
    outcome = attr.ib(type=TaskOutcome)
    exc_info = attr.ib(default=None, type=Optional[ExceptionInfo])
    sections = attr.ib(factory=list, type=List[Tuple[str, str, str]])

    @classmethod
    def from_task_and_exception(
        cls, task: "MetaTask", exc_info: ExceptionInfo
    ) -> "ExecutionReport":
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(task, TaskOutcome.FAIL, exc_info, task._report_sections)

    @classmethod
    def from_task(cls, task: "MetaTask") -> "ExecutionReport":
        return cls(task, TaskOutcome.SUCCESS, None, task._report_sections)
