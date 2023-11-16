from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from _pytask.collect_utils import collect_dependency
from _pytask.dag_utils import TopologicalSorter
from _pytask.models import NodeInfo
from _pytask.node_protocols import PDelayedNode
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.nodes import Task
from _pytask.reports import ExecutionReport
from _pytask.tree_util import PyTree
from _pytask.tree_util import tree_map_with_path

if TYPE_CHECKING:
    from _pytask.session import Session


TASKS_WITH_DELAYED_NODES = set()


def collect_delayed_nodes(
    session: Session, task: PTask, node: Any, path: tuple[Any, ...]
) -> PyTree[PNode]:
    """Collect delayed nodes.

    1. Call the :meth:`pytask.PDelayedNode.collect` to receive the raw nodes.
    2. Collect the raw nodes as usual.

    """
    if not isinstance(node, PDelayedNode):
        return node

    # Add task to register to update the DAG after the task is executed.
    TASKS_WITH_DELAYED_NODES.add(task.signature)

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


def recreate_dag(session: Session, task: PTask) -> None:
    """Recreate the DAG."""
    try:
        session.dag = session.hook.pytask_dag_create_dag(
            session=session, tasks=session.tasks
        )
        session.hook.pytask_dag_modify_dag(session=session, dag=session.dag)
        session.scheduler = TopologicalSorter.from_dag_and_sorter(
            session.dag, session.scheduler
        )

    except Exception:  # noqa: BLE001
        report = ExecutionReport.from_task_and_exception(task, sys.exc_info())
        session.execution_reports.append(report)
        session.should_stop = True


def collect_delayed_products(session: Session, task: PTask) -> None:
    """Collect delayed products.

    Unfortunately, this function needs to be called when a task finishes successfully
    (skipped unchanged, persisted, etc..).

    """
    # Replace delayed nodes with their actually resolved nodes.
    task.produces = tree_map_with_path(  # type: ignore[assignment]
        lambda p, x: collect_delayed_nodes(session, task, x, p), task.produces
    )

    if task.signature in TASKS_WITH_DELAYED_NODES:
        recreate_dag(session, task)
