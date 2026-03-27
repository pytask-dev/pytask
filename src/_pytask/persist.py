"""Implement the ability for tasks to persist."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from _pytask.dag_utils import node_and_neighbors
from _pytask.mark_utils import has_mark
from _pytask.node_protocols import PProvisionalNode
from _pytask.outcomes import Persisted
from _pytask.outcomes import TaskOutcome
from _pytask.pluginmanager import hookimpl
from _pytask.provisional_utils import collect_provisional_products
from _pytask.state import has_node_changed
from _pytask.state import update_states

if TYPE_CHECKING:
    from _pytask.node_protocols import PNode
    from _pytask.node_protocols import PTask
    from _pytask.reports import ExecutionReport
    from _pytask.session import Session


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Add the marker to the configuration."""
    config["markers"]["persist"] = (
        "Prevent execution of a task if all products exist and even if something has "
        "changed (dependencies, source file, products). This decorator might be useful "
        "for expensive tasks where only the formatting of the file has changed. The "
        "state of the files which have changed will also be remembered and another run "
        "will skip the task with success."
    )


@hookimpl
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Exit persisting tasks early.

    This check needs to run after the same hook implementation that resolves provisional
    dependencies and before the same hook implementation for skipping tasks.

    """
    if has_mark(task, "persist"):
        stateful_nodes: list[tuple[PTask | PNode, str | None]] = []
        for name in node_and_neighbors(session.dag, task.signature):
            node = session.dag.nodes[name]
            if isinstance(node, PProvisionalNode):
                continue
            stateful_nodes.append((node, node.state()))

        all_states = [state for _, state in stateful_nodes]
        all_nodes_exist = all(all_states)

        if all_nodes_exist:
            any_node_changed = any(
                has_node_changed(
                    session=session,
                    task=task,
                    node=node,
                    state=state,
                )
                for node, state in stateful_nodes
            )
            if any_node_changed:
                collect_provisional_products(session, task)
                raise Persisted


@hookimpl
def pytask_execute_task_process_report(
    session: Session, report: ExecutionReport
) -> bool | None:
    """Set task status to success.

    Do not return ``True`` so that states will be updated in database.

    """
    if report.exc_info and isinstance(report.exc_info[1], Persisted):
        report.outcome = TaskOutcome.PERSISTENCE
        update_states(session, report.task)
        return True
    return None
