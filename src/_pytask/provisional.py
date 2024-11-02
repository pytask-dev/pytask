"""Contains hook implementations for provisional nodes and task generators."""

from __future__ import annotations

import inspect
import sys
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from _pytask.config import hookimpl
from _pytask.exceptions import NodeLoadError
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.outcomes import CollectionOutcome
from _pytask.provisional_utils import TASKS_WITH_PROVISIONAL_NODES
from _pytask.provisional_utils import collect_provisional_nodes
from _pytask.provisional_utils import recreate_dag
from _pytask.reports import ExecutionReport
from _pytask.task_utils import COLLECTED_TASKS
from _pytask.task_utils import parse_collected_tasks_with_task_marker
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_map_with_path
from _pytask.typing import is_task_generator
from pytask import TaskOutcome

if TYPE_CHECKING:
    from collections.abc import Mapping

    from _pytask.session import Session


@hookimpl(tryfirst=True)
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Collect provisional nodes and parse them.

    Provisional nodes need to be resolved before the same hook in persist.

    """
    task.depends_on = tree_map_with_path(  # type: ignore[assignment]
        lambda p, x: collect_provisional_nodes(session, task, x, p), task.depends_on
    )
    if task.signature in TASKS_WITH_PROVISIONAL_NODES:
        recreate_dag(session, task)


def _safe_load(node: PNode | PProvisionalNode, task: PTask, is_product: bool) -> Any:
    try:
        return node.load(is_product=is_product)
    except Exception as e:
        msg = f"Exception while loading node {node.name!r} of task {task.name!r}"
        raise NodeLoadError(msg) from e


@hookimpl
def pytask_execute_task(session: Session, task: PTask) -> None:
    """Execute task generators and collect the tasks."""
    if is_task_generator(task):
        kwargs = {}
        for name, value in task.depends_on.items():
            kwargs[name] = tree_map(lambda x: _safe_load(x, task, False), value)

        parameters = inspect.signature(task.function).parameters
        for name, value in task.produces.items():
            if name in parameters:
                kwargs[name] = tree_map(lambda x: _safe_load(x, task, True), value)

        task.execute(**kwargs)

        # Parse tasks created with @task.
        name_to_function: Mapping[str, Callable[..., Any] | PTask]
        if isinstance(task, PTaskWithPath) and task.path in COLLECTED_TASKS:
            tasks = COLLECTED_TASKS.pop(task.path)
            name_to_function = parse_collected_tasks_with_task_marker(tasks)
        elif None in COLLECTED_TASKS:
            tasks = COLLECTED_TASKS.pop(None)
            name_to_function = parse_collected_tasks_with_task_marker(tasks)
        else:
            msg = "The task generator {task.name!r} did not create any tasks."
            raise RuntimeError(msg)

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


@hookimpl
def pytask_execute_task_process_report(report: ExecutionReport) -> bool | None:
    """Prevent update of states for successful task generators.

    It also leads to task generators always being executed, but we have an additional
    switch implemented in ``pytask_execute_task_setup``.

    """
    task = report.task
    if report.outcome == TaskOutcome.SUCCESS and is_task_generator(task):
        return True
    return None


@hookimpl
def pytask_unconfigure() -> None:
    """Clear the global variable after execution."""
    TASKS_WITH_PROVISIONAL_NODES.clear()
