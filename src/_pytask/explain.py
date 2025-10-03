"""Contains logic for explaining why tasks need to be re-executed."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from attrs import define
from attrs import field
from rich.text import Text

from _pytask.console import console
from _pytask.outcomes import TaskOutcome
from _pytask.pluginmanager import hookimpl

if TYPE_CHECKING:
    from _pytask.node_protocols import PNode
    from _pytask.node_protocols import PTask
    from _pytask.reports import ExecutionReport
    from _pytask.session import Session


@define
class ChangeReason:
    """Represents a reason why a node changed."""

    node_name: str
    node_type: str  # "source", "dependency", "product", "task"
    reason: str  # "changed", "missing", "not_in_db", "first_run"
    details: dict[str, Any] = field(factory=dict)

    def format(self, verbose: int = 1) -> str:  # noqa: PLR0911
        """Format the change reason as a string."""
        if self.reason == "missing":
            return f"  • {self.node_name}: Missing"
        if self.reason == "not_in_db":
            return (
                f"  • {self.node_name}: Not in database (first run or database cleared)"
            )
        if self.reason == "changed":
            if verbose >= 2 and "old_hash" in self.details:  # noqa: PLR2004
                return (
                    f"  • {self.node_name}: Changed\n"
                    f"    Previous hash: {self.details['old_hash'][:8]}...\n"
                    f"    Current hash:  {self.details['new_hash'][:8]}..."
                )
            return f"  • {self.node_name}: Changed"
        if self.reason == "first_run":
            return "  • First execution"
        if self.reason == "forced":
            return "  • Forced execution (--force flag)"
        return f"  • {self.node_name}: {self.reason}"


@define
class TaskExplanation:
    """Represents the explanation for why a task needs to be executed."""

    task_name: str
    would_execute: bool
    outcome: TaskOutcome | None = None
    reasons: list[ChangeReason] = field(factory=list)

    def format(self, verbose: int = 1) -> str:
        """Format the task explanation as a string."""
        lines = []

        if self.outcome == TaskOutcome.SKIP_UNCHANGED:
            lines.append(f"{self.task_name}")
            lines.append("  ✓ No changes detected")
        elif self.outcome == TaskOutcome.PERSISTENCE:
            lines.append(f"{self.task_name}")
            lines.append("  • Persisted (products exist, changes ignored)")
        elif self.outcome == TaskOutcome.SKIP:
            lines.append(f"{self.task_name}")
            lines.append("  • Skipped by marker")
        elif not self.reasons:
            lines.append(f"{self.task_name}")
            lines.append("  ✓ No changes detected")
        else:
            lines.append(f"{self.task_name}")
            lines.extend(reason.format(verbose) for reason in self.reasons)

        return "\n".join(lines)


def create_change_reason(
    node: PNode | PTask,
    node_type: str,
    reason: str,
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
def pytask_execute_log_end(session: Session, reports: list[ExecutionReport]) -> None:
    """Log explanations if --explain flag is set."""
    if not session.config["explain"]:
        return

    console.print()
    console.rule(Text("Explanation", style="bold blue"), style="bold blue")
    console.print()

    # Collect all explanations
    explanations = [
        report.task._explanation
        for report in reports
        if hasattr(report.task, "_explanation")
    ]

    if not explanations:
        console.print("No tasks require execution - everything is up to date.")
        return

    # Group by outcome
    would_execute = [e for e in explanations if e.would_execute]
    skipped = [
        e
        for e in explanations
        if not e.would_execute and e.outcome != TaskOutcome.SKIP_UNCHANGED
    ]
    unchanged = [e for e in explanations if e.outcome == TaskOutcome.SKIP_UNCHANGED]

    verbose = session.config.get("verbose", 1)

    if would_execute:
        # WOULD_BE_EXECUTED has style "success" in TaskOutcome
        console.print(
            Text(
                "Tasks that would be executed:",
                style=TaskOutcome.WOULD_BE_EXECUTED.style,
            ),
        )
        console.print()
        for exp in would_execute:
            console.print(exp.format(verbose))
            console.print()

    if skipped:
        # SKIP has style "skipped" in TaskOutcome
        console.print(Text("Skipped tasks:", style=TaskOutcome.SKIP.style))
        console.print()
        for exp in skipped:
            console.print(exp.format(verbose))
            console.print()

    if unchanged and verbose >= 2:  # noqa: PLR2004
        # SKIP_UNCHANGED has style "success" in TaskOutcome
        console.print(
            Text("Tasks with no changes:", style=TaskOutcome.SKIP_UNCHANGED.style)
        )
        console.print()
        for exp in unchanged:
            console.print(exp.format(verbose))
            console.print()
