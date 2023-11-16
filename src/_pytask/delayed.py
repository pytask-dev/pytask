from __future__ import annotations

import sys
from typing import Any
from typing import TYPE_CHECKING

from _pytask.config import hookimpl
from _pytask.delayed_utils import collect_delayed_nodes
from _pytask.delayed_utils import recreate_dag
from _pytask.delayed_utils import TASKS_WITH_DELAYED_NODES
from _pytask.exceptions import NodeLoadError
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.outcomes import CollectionOutcome
from _pytask.reports import ExecutionReport
from _pytask.task_utils import parse_collected_tasks_with_task_marker
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_map_with_path

if TYPE_CHECKING:
    from _pytask.session import Session


@hookimpl
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Collect delayed nodes and parse them."""
    task.depends_on = tree_map_with_path(  # type: ignore[assignment]
        lambda p, x: collect_delayed_nodes(session, task, x, p), task.depends_on
    )
    if task.signature in TASKS_WITH_DELAYED_NODES:
        recreate_dag(session, task)


def _safe_load(node: PNode, task: PTask, is_product: bool) -> Any:
    try:
        return node.load(is_product=is_product)
    except Exception as e:  # noqa: BLE001
        msg = f"Exception while loading node {node.name!r} of task {task.name!r}"
        raise NodeLoadError(msg) from e


@hookimpl
def pytask_execute_task(session: Session, task: PTask) -> None:
    """Execute task generators and collect the tasks."""
    is_generator = task.attributes.get("is_generator", False)
    if is_generator:
        kwargs = {}
        for name, value in task.depends_on.items():
            kwargs[name] = tree_map(lambda x: _safe_load(x, task, False), value)

        new_tasks = list(task.execute(**kwargs))

        name_to_function = parse_collected_tasks_with_task_marker(new_tasks)

        new_reports = []
        for name, function in name_to_function.items():
            report = session.hook.pytask_collect_task_protocol(
                session=session,
                reports=session.collection_reports,
                path=task.path if isinstance(task, PTaskWithPath) else None,
                name=name,
                obj=function,
            )
            new_reports.append(report)

        session.tasks.extend(
            i.node
            for i in new_reports
            if i.outcome == CollectionOutcome.SUCCESS and isinstance(i.node, PTask)
        )

        try:
            session.hook.pytask_collect_modify_tasks(
                session=session, tasks=session.tasks
            )
        except Exception:  # noqa: BLE001  # pragma: no cover
            report = ExecutionReport.from_task_and_exception(
                task=task, exc_info=sys.exc_info()
            )
        session.collection_reports.append(report)

        recreate_dag(session, task)
