"""Implement the ability for tasks to persist."""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from _pytask.config import hookimpl
from _pytask.dag import node_and_neighbors
from _pytask.database import update_states_in_database
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark_utils import has_mark
from _pytask.outcomes import Persisted
from _pytask.outcomes import TaskOutcome


if TYPE_CHECKING:
    from _pytask.session import Session
    from _pytask.nodes import Task
    from _pytask.report import ExecutionReport


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
def pytask_execute_task_setup(session: Session, task: Task) -> None:
    """Exit persisting tasks early.

    The decorator needs to be set and all nodes need to exist.

    """
    if has_mark(task, "persist"):
        try:
            for name in node_and_neighbors(session.dag, task.name):
                node = (
                    session.dag.nodes[name].get("task")
                    or session.dag.nodes[name]["node"]
                )
                node.state()
        except NodeNotFoundError:
            all_nodes_exist = False
        else:
            all_nodes_exist = True

        if all_nodes_exist:
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
        update_states_in_database(session.dag, report.task.name)
        return True
    return None
