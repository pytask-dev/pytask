"""Contains everything related to reports."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import ClassVar

from attrs import define
from attrs import field
from rich.rule import Rule
from rich.text import Text

from _pytask.capture_utils import ShowCapture
from _pytask.console import format_task_name
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.traceback import OptionalExceptionInfo
from _pytask.traceback import Traceback

if TYPE_CHECKING:
    from rich.console import Console
    from rich.console import ConsoleOptions
    from rich.console import RenderResult

    from _pytask.node_protocols import PNode
    from _pytask.node_protocols import PProvisionalNode
    from _pytask.node_protocols import PTask


@define
class CollectionReport:
    """A collection report for a task."""

    outcome: CollectionOutcome
    node: PTask | PNode | PProvisionalNode | None = None
    exc_info: OptionalExceptionInfo | None = None

    @classmethod
    def from_exception(
        cls: type[CollectionReport],
        outcome: CollectionOutcome,
        exc_info: OptionalExceptionInfo,
        node: PTask | PNode | PProvisionalNode | None = None,
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

    editor_url_scheme: ClassVar[str] = "file"
    show_locals: ClassVar[bool] = False
    show_capture: ClassVar[ShowCapture] = ShowCapture.ALL

    @classmethod
    def from_task_and_exception(
        cls, task: PTask, exc_info: OptionalExceptionInfo
    ) -> ExecutionReport:
        """Create a report from a task and an exception."""
        return cls(task, TaskOutcome.FAIL, exc_info, task.report_sections)

    @classmethod
    def from_task(cls, task: PTask) -> ExecutionReport:
        """Create a report from a task."""
        return cls(task, TaskOutcome.SUCCESS, None, task.report_sections)

    def __rich_console__(
        self, console: Console, console_options: ConsoleOptions
    ) -> RenderResult:
        task_name = format_task_name(
            task=self.task, editor_url_scheme=self.editor_url_scheme
        )
        text = Text.assemble("Task ", task_name, " failed", style="failed")
        traceback = Traceback(self.exc_info)  # type: ignore[arg-type]

        yield Rule(text, style=self.outcome.style)
        yield ""
        yield traceback
        yield ""

        for when, key, content in self.sections:
            if key in ("stdout", "stderr") and self.show_capture in (
                ShowCapture(key),
                ShowCapture.ALL,
            ):
                yield Rule(f"Captured {key} during {when}", style="default")
                yield content
