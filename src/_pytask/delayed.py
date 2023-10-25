from __future__ import annotations

from typing import TYPE_CHECKING

from _pytask.config import hookimpl
from _pytask.node_protocols import PTask
from _pytask.outcomes import CollectionOutcome

if TYPE_CHECKING:
    from _pytask.session import Session


@hookimpl
def pytask_execute_collect_delayed_tasks(session: Session) -> None:
    """Collect tasks that are delayed."""
    # Separate ready and delayed tasks.
    still_delayed_tasks = []
    ready_tasks = []

    for delayed_task in session.delayed_tasks:
        if delayed_task.obj.pytask_meta.is_ready():
            ready_tasks.append(delayed_task)
        else:
            still_delayed_tasks.append(delayed_task)

    session.delayed_tasks = still_delayed_tasks

    if not ready_tasks:
        return

    # Collect tasks that are now ready.
    new_collection_reports = []
    for ready_task in ready_tasks:
        report = session.hook.pytask_collect_task_protocol(
            session=session,
            reports=session.collection_reports,
            path=ready_task.path,
            name=ready_task.name,
            obj=ready_task.obj,
        )

        if report is not None:
            new_collection_reports.append(report)

    # What to do with failed tasks? Can we just add them to executionreports.

    # Add new tasks.
    session.tasks.extend(
        i.node
        for i in session.collection_reports
        if i.outcome == CollectionOutcome.SUCCESS and isinstance(i.node, PTask)
    )

    session.hook.pytask_dag(session=session)
