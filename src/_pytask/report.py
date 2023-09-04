"""Contains everything related to reports."""
from __future__ import annotations

from types import TracebackType
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from attrs import define
from attrs import field


if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from _pytask.node_protocols import MetaNode


ExceptionInfo = Tuple[Type[BaseException], BaseException, Union[TracebackType, None]]


@define
class CollectionReport:
    """A collection report for a task."""

    outcome: CollectionOutcome
    node: MetaNode | None = None
    exc_info: ExceptionInfo | None = None

    @classmethod
    def from_exception(
        cls: type[CollectionReport],
        outcome: CollectionOutcome,
        exc_info: ExceptionInfo,
        node: MetaNode | None = None,
    ) -> CollectionReport:
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(outcome=outcome, node=node, exc_info=exc_info)


@define
class DagReport:
    """A report for an error during the creation of the DAG."""

    exc_info: ExceptionInfo

    @classmethod
    def from_exception(cls, exc_info: ExceptionInfo) -> DagReport:
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(exc_info)


@define
class ExecutionReport:
    """A report for an executed task."""

    task: PTask
    outcome: TaskOutcome
    exc_info: ExceptionInfo | None = None
    sections: list[tuple[str, str, str]] = field(factory=list)

    @classmethod
    def from_task_and_exception(
        cls, task: PTask, exc_info: ExceptionInfo
    ) -> ExecutionReport:
        """Create a report from a task and an exception."""
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(task, TaskOutcome.FAIL, exc_info, task.report_sections)

    @classmethod
    def from_task(cls, task: PTask) -> ExecutionReport:
        """Create a report from a task."""
        return cls(task, TaskOutcome.SUCCESS, None, task.report_sections)
