"""Contains everything related to reports."""
from __future__ import annotations

from typing import Protocol
from typing import runtime_checkable
from typing import TYPE_CHECKING

from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.traceback import OptionalExceptionInfo
from _pytask.traceback import remove_internal_traceback_frames_from_exc_info
from _pytask.traceback import Traceback
from attrs import define
from attrs import field
from rich.rule import Rule
from rich.text import Text


if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from rich.console import Console
    from rich.console import RenderResult
    from rich.console import ConsoleOptions
    from _pytask.node_protocols import MetaNode


@runtime_checkable
class PReport(Protocol):
    """The protocol for reports."""

    outcome: CollectionOutcome | TaskOutcome
    node: MetaNode | None = None
    exc_info: OptionalExceptionInfo | None = None

    def __rich_console__(
        self, console: Console, console_options: ConsoleOptions
    ) -> RenderResult:
        """Render a report."""
        ...


@define
class CollectionReport:
    """A collection report for a task."""

    outcome: CollectionOutcome
    node: MetaNode | None = None
    exc_info: OptionalExceptionInfo | None = None

    @classmethod
    def from_exception(
        cls: type[CollectionReport],
        outcome: CollectionOutcome,
        exc_info: OptionalExceptionInfo,
        node: MetaNode | None = None,
    ) -> CollectionReport:
        return cls(outcome=outcome, node=node, exc_info=exc_info)

    def __rich_console__(
        self, console: Console, console_options: ConsoleOptions
    ) -> RenderResult:
        header = "Error" if self.node is None else f"Could not collect {self.node.name}"
        traceback = Traceback(self.exc_info)  # type: ignore[arg-type]
        yield Rule(
            Text(header, style=CollectionOutcome.FAIL.style),
            style=CollectionOutcome.FAIL.style,
        )
        yield ""
        yield traceback
        yield ""


@define
class DagReport:
    """A report for an error during the creation of the DAG."""

    exc_info: OptionalExceptionInfo

    @classmethod
    def from_exception(cls, exc_info: OptionalExceptionInfo) -> DagReport:
        return cls(exc_info)

    def __rich_console__(
        self, console: Console, console_options: ConsoleOptions
    ) -> RenderResult:
        traceback = Traceback(self.exc_info)
        yield traceback


@define
class ExecutionReport:
    """A report for an executed task."""

    task: PTask
    outcome: TaskOutcome
    exc_info: OptionalExceptionInfo | None = None
    sections: list[tuple[str, str, str]] = field(factory=list)

    @classmethod
    def from_task_and_exception(
        cls, task: PTask, exc_info: OptionalExceptionInfo
    ) -> ExecutionReport:
        """Create a report from a task and an exception."""
        exc_info = remove_internal_traceback_frames_from_exc_info(exc_info)
        return cls(task, TaskOutcome.FAIL, exc_info, task.report_sections)

    @classmethod
    def from_task(cls, task: PTask) -> ExecutionReport:
        """Create a report from a task."""
        return cls(task, TaskOutcome.SUCCESS, None, task.report_sections)
