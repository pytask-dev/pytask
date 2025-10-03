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
        if self.reason == "cascade":
            return f"  • Preceding {self.node_name} would be executed"
        return f"  • {self.node_name}: {self.reason}"


@define
class TaskExplanation:
    """Represents the explanation for why a task needs to be executed."""

    reasons: list[ChangeReason] = field(factory=list)

    def format(self, task_name: str, outcome: TaskOutcome, verbose: int = 1) -> str:
        """Format the task explanation as a string."""
        lines = []

        if outcome == TaskOutcome.SKIP_UNCHANGED:
            lines.append(f"{task_name}")
            lines.append("  ✓ No changes detected")
        elif outcome == TaskOutcome.PERSISTENCE:
            lines.append(f"{task_name}")
            lines.append("  • Persisted (products exist, changes ignored)")
        elif outcome == TaskOutcome.SKIP:
            lines.append(f"{task_name}")
            lines.append("  • Skipped by marker")
        elif not self.reasons:
            lines.append(f"{task_name}")
            lines.append("  ✓ No changes detected")
        else:
            lines.append(f"{task_name}")
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
def pytask_execute_log_end(  # noqa: C901
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
            console.print(explanation.format(report.task.name, report.outcome, verbose))
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
            console.print(explanation.format(report.task.name, report.outcome, verbose))
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
            console.print(explanation.format(report.task.name, report.outcome, verbose))
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
            console.print(explanation.format(report.task.name, report.outcome, verbose))
            console.print()
    elif unchanged and verbose == 1:
        console.print(
            f"{len(unchanged)} task(s) with no changes (use -vv to show details)",
            highlight=False,
        )
