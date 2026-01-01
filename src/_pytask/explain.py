"""Contains logic for explaining why tasks need to be re-executed."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal

from rich.text import Text

from _pytask.console import console
from _pytask.console import format_task_name
from _pytask.outcomes import TaskOutcome
from _pytask.pluginmanager import hookimpl

if TYPE_CHECKING:
    from collections.abc import Iterator

    from rich.console import Console
    from rich.console import ConsoleOptions
    from rich.console import RenderableType

    from _pytask.node_protocols import PNode
    from _pytask.node_protocols import PTask
    from _pytask.reports import ExecutionReport
    from _pytask.session import Session


NodeType = Literal["source", "dependency", "product", "task"]
ReasonType = Literal[
    "changed", "missing", "not_in_db", "first_run", "forced", "cascade"
]


@dataclass
class ChangeReason:
    """Represents a reason why a node changed."""

    node_name: str
    node_type: NodeType
    reason: ReasonType
    details: dict[str, Any] = field(default_factory=dict)
    verbose: int = 1

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> Iterator[RenderableType]:
        """Render the change reason using Rich protocol."""
        if self.reason == "missing":
            yield Text(f"  • {self.node_name}: Missing")
        elif self.reason == "not_in_db":
            yield Text(
                f"  • {self.node_name}: Not in database (first run or database cleared)"
            )
        elif self.reason == "changed":
            if self.verbose >= 2 and "old_hash" in self.details:  # noqa: PLR2004
                yield Text(f"  • {self.node_name}: Changed")
                yield Text(f"    Previous hash: {self.details['old_hash'][:8]}...")
                yield Text(f"    Current hash:  {self.details['new_hash'][:8]}...")
            else:
                yield Text(f"  • {self.node_name}: Changed")
        elif self.reason == "first_run":
            yield Text("  • First execution")
        elif self.reason == "forced":
            yield Text("  • Forced execution (--force flag)")
        elif self.reason == "cascade":
            yield Text(f"  • Preceding {self.node_name} would be executed")
        else:
            yield Text(f"  • {self.node_name}: {self.reason}")


@dataclass
class TaskExplanation:
    """Represents the explanation for why a task needs to be executed."""

    reasons: list[ChangeReason] = field(default_factory=list)
    task: PTask | None = None
    outcome: TaskOutcome | None = None
    verbose: int = 1
    editor_url_scheme: str = ""

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> Iterator[RenderableType]:
        """Render the task explanation using Rich protocol."""
        # Format task name with proper styling and links
        if self.task:
            yield format_task_name(self.task, self.editor_url_scheme)
        else:
            yield Text("Unknown task")

        # Add explanation based on outcome
        if self.outcome == TaskOutcome.SKIP_UNCHANGED:
            yield Text("  ✓ No changes detected")
        elif self.outcome == TaskOutcome.PERSISTENCE:
            yield Text("  • Persisted (products exist, changes ignored)")
        elif self.outcome == TaskOutcome.SKIP:
            yield Text("  • Skipped by marker")
        elif not self.reasons:
            yield Text("  ✓ No changes detected")
        else:
            for reason in self.reasons:
                reason.verbose = self.verbose
                yield reason


def create_change_reason(
    node: PNode | PTask,
    node_type: NodeType,
    reason: ReasonType,
    old_hash: str | None = None,
    new_hash: str | None = None,
) -> ChangeReason:
    """Create a ChangeReason object."""
    details = {}
    if old_hash is not None:
        details["old_hash"] = old_hash
    if new_hash is not None:
        details["new_hash"] = new_hash

    return ChangeReason(
        node_name=node.name,
        node_type=node_type,
        reason=reason,
        details=details,
    )


@hookimpl(tryfirst=True)
def pytask_execute_log_end(  # noqa: C901, PLR0915
    session: Session, reports: list[ExecutionReport]
) -> None:
    """Log explanations if --explain flag is set."""
    if not session.config["explain"]:
        return

    console.print()
    console.rule(Text("Explanation", style="bold blue"), style="bold blue")
    console.print()

    # Collect all reports with explanations
    reports_with_explanations = [
        report for report in reports if "explanation" in report.task.attributes
    ]

    if not reports_with_explanations:
        console.print("No tasks require execution - everything is up to date.")
        return

    # Group by outcome
    would_execute = [
        r
        for r in reports_with_explanations
        if r.outcome == TaskOutcome.WOULD_BE_EXECUTED
    ]
    skipped = [
        r
        for r in reports_with_explanations
        if r.outcome in (TaskOutcome.SKIP, TaskOutcome.SKIP_PREVIOUS_FAILED)
    ]
    unchanged = [
        r for r in reports_with_explanations if r.outcome == TaskOutcome.SKIP_UNCHANGED
    ]
    persisted = [
        r for r in reports_with_explanations if r.outcome == TaskOutcome.PERSISTENCE
    ]

    verbose = session.config.get("verbose", 1)
    editor_url_scheme = session.config.get("editor_url_scheme", "no_link")

    if would_execute:
        console.rule(
            Text(
                "─── Tasks that would be executed",
                style=TaskOutcome.WOULD_BE_EXECUTED.style,
            ),
            align="left",
            style=TaskOutcome.WOULD_BE_EXECUTED.style,
        )
        console.print()
        for report in would_execute:
            explanation = report.task.attributes["explanation"]
            explanation.task = report.task
            explanation.outcome = report.outcome
            explanation.verbose = verbose
            explanation.editor_url_scheme = editor_url_scheme
            console.print(explanation)
            console.print()

    if skipped:
        console.rule(
            Text("─── Skipped tasks", style=TaskOutcome.SKIP.style),
            align="left",
            style=TaskOutcome.SKIP.style,
        )
        console.print()
        for report in skipped:
            explanation = report.task.attributes["explanation"]
            explanation.task = report.task
            explanation.outcome = report.outcome
            explanation.verbose = verbose
            explanation.editor_url_scheme = editor_url_scheme
            console.print(explanation)
            console.print()

    if persisted and verbose >= 2:  # noqa: PLR2004
        console.rule(
            Text("─── Persisted tasks", style=TaskOutcome.PERSISTENCE.style),
            align="left",
            style=TaskOutcome.PERSISTENCE.style,
        )
        console.print()
        for report in persisted:
            explanation = report.task.attributes["explanation"]
            explanation.task = report.task
            explanation.outcome = report.outcome
            explanation.verbose = verbose
            explanation.editor_url_scheme = editor_url_scheme
            console.print(explanation)
            console.print()
    elif persisted and verbose == 1:
        console.print(
            f"{len(persisted)} persisted task(s) (use -vv to show details)",
            highlight=False,
        )

    if unchanged and verbose >= 2:  # noqa: PLR2004
        console.rule(
            Text("─── Tasks with no changes", style=TaskOutcome.SKIP_UNCHANGED.style),
            align="left",
            style=TaskOutcome.SKIP_UNCHANGED.style,
        )
        console.print()
        for report in unchanged:
            explanation = report.task.attributes["explanation"]
            explanation.task = report.task
            explanation.outcome = report.outcome
            explanation.verbose = verbose
            explanation.editor_url_scheme = editor_url_scheme
            console.print(explanation)
            console.print()
    elif unchanged and verbose == 1:
        console.print(
            f"{len(unchanged)} task(s) with no changes (use -vv to show details)",
            highlight=False,
        )
