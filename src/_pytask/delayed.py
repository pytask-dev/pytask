from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from _pytask.collect_utils import collect_dependency
from _pytask.config import hookimpl
from _pytask.exceptions import NodeLoadError
from _pytask.models import NodeInfo
from _pytask.node_protocols import PDelayedNode
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.nodes import Task
from _pytask.outcomes import CollectionOutcome
from _pytask.reports import ExecutionReport
from _pytask.tree_util import PyTree
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_map_with_path

if TYPE_CHECKING:
    from _pytask.session import Session


_TASKS_WITH_DELAYED_NODES = set()


@hookimpl
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Collect delayed nodes and parse them."""
    task.depends_on = tree_map_with_path(  # type: ignore[assignment]
        lambda p, x: _collect_delayed_nodes(session, task, x, p), task.depends_on
    )
    if task.signature in _TASKS_WITH_DELAYED_NODES:
        _recreate_dag(session, task)


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

        new_reports = []
        for raw_task in new_tasks:
            report = session.hook.pytask_collect_task_protocol(
                session=session,
                reports=session.collection_reports,
                path=task.path if isinstance(task, PTaskWithPath) else None,
                name=name,
                obj=raw_task,
            )
            new_reports.append(report)

        session.tasks.extend(
            i.node
            for i in new_reports
            if i.outcome == CollectionOutcome.SUCCESS and isinstance(i.node, PTask)
        )


@hookimpl
def pytask_execute_task_teardown(session: Session, task: PTask) -> None:
    """Check if nodes are produced by a task."""
    # Replace delayed nodes with their actually resolved nodes.
    task.produces = tree_map_with_path(  # type: ignore[assignment]
        lambda p, x: _collect_delayed_nodes(session, task, x, p), task.produces
    )

    if task.signature in _TASKS_WITH_DELAYED_NODES:
        _recreate_dag(session, task)


def _collect_delayed_nodes(
    session: Session, task: PTask, node: Any, path: tuple[Any, ...]
) -> PyTree[PNode]:
    """Collect delayed nodes.

    1. Call the :meth:`pytask.PDelayedNode.collect` to receive the raw nodes.
    2. Collect the raw nodes as usual.

    """
    if not isinstance(node, PDelayedNode):
        return node

    # Add task to register to update the DAG after the task is executed.
    _TASKS_WITH_DELAYED_NODES.add(task.signature)

    # Collect delayed nodes and receive raw nodes.
    delayed_nodes = node.collect()

    # Collect raw nodes.
    node_path = task.path.parent if isinstance(task, PTaskWithPath) else Path.cwd()
    task_name = task.base_name if isinstance(task, Task) else task.name
    task_path = task.path if isinstance(task, PTaskWithPath) else None
    arg_name, *rest_path = path

    return tree_map_with_path(
        lambda p, x: collect_dependency(
            session,
            node_path,
            task_name,
            NodeInfo(
                arg_name=arg_name,
                path=(*rest_path, *p),
                value=x,
                task_path=task_path,
                task_name=task_name,
            ),
        ),
        delayed_nodes,
    )


def _recreate_dag(session: Session, task: PTask) -> None:
    """Recreate the DAG."""
    try:
        session.dag = session.hook.pytask_dag_create_dag(
            session=session, tasks=session.tasks
        )
        session.hook.pytask_dag_modify_dag(session=session, dag=session.dag)

    except Exception:  # noqa: BLE001
        report = ExecutionReport.from_task_and_exception(task, sys.exc_info())
        session.execution_reports.append(report)
        session.should_stop = True
