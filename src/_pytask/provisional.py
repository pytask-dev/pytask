"""Contains hook implementations for provisional nodes and task generators."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING
from typing import Any

from _pytask.config import hookimpl
from _pytask.dag import create_dag_from_session
from _pytask.exceptions import CollectionError
from _pytask.exceptions import NodeLoadError
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.outcomes import CollectionOutcome
from _pytask.provisional_utils import TASKS_WITH_PROVISIONAL_NODES
from _pytask.provisional_utils import collect_provisional_nodes
from _pytask.provisional_utils import recreate_dag
from _pytask.task_utils import COLLECTED_TASKS
from _pytask.task_utils import parse_collected_tasks_with_task_marker
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_map_with_path
from _pytask.typing import is_task_generator
from pytask import TaskOutcome

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

    from _pytask.reports import CollectionReport
    from _pytask.reports import ExecutionReport
    from _pytask.session import Session


@hookimpl(tryfirst=True)
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Collect provisional nodes and parse them.

    Provisional nodes need to be resolved before the same hook in persist.

    """
    task.depends_on = tree_map_with_path(
        lambda p, x: collect_provisional_nodes(session, task, x, p),
        task.depends_on,
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
def pytask_execute_task(session: Session, task: PTask) -> bool | None:
    """Execute task generators and collect the tasks."""
    if not is_task_generator(task):
        return None

    kwargs = {}
    for name, value in task.depends_on.items():
        kwargs[name] = tree_map(lambda x: _safe_load(x, task, False), value)

    parameters = inspect.signature(task.function).parameters
    for name, value in task.produces.items():
        if name in parameters:
            kwargs[name] = tree_map(lambda x: _safe_load(x, task, True), value)

    task.execute(**kwargs)

    name_to_function: Mapping[str, Callable[..., Any] | PTask]
    if isinstance(task, PTaskWithPath) and task.path in COLLECTED_TASKS:
        tasks = COLLECTED_TASKS.pop(task.path)
        name_to_function = parse_collected_tasks_with_task_marker(tasks)
    elif None in COLLECTED_TASKS:
        tasks = COLLECTED_TASKS.pop(None)
        name_to_function = parse_collected_tasks_with_task_marker(tasks)
    else:
        msg = f"The task generator {task.name!r} did not create any tasks."
        raise RuntimeError(msg)

    new_reports: list[CollectionReport] = []
    for name, function in name_to_function.items():
        report = session.hook.pytask_collect_task_protocol(
            session=session,
            reports=new_reports,
            path=task.path if isinstance(task, PTaskWithPath) else None,
            name=name,
            obj=function,
        )
        if report is not None:
            new_reports.append(report)

    session.collection_reports.extend(new_reports)
    failed_reports = [
        report for report in new_reports if report.outcome == CollectionOutcome.FAIL
    ]
    if failed_reports:
        _raise_error_for_failed_generated_tasks(task, failed_reports)

    generated_tasks = [
        report.node
        for report in new_reports
        if report.outcome == CollectionOutcome.SUCCESS
        and isinstance(report.node, PTask)
    ]
    _commit_generated_tasks(session, generated_tasks)
    return True


def _raise_error_for_failed_generated_tasks(
    task: PTask, reports: list[CollectionReport]
) -> None:
    """Raise one generator error containing every child collection failure."""
    lines = [f"The task generator {task.name!r} created tasks that failed collection:"]
    for report in reports:
        assert report.exc_info is not None
        exception = report.exc_info[1]
        node_name = report.node.name if report.node is not None else "<unknown>"
        lines.append(f"- {node_name!r}: {type(exception).__name__}: {exception}")

    error = CollectionError("\n".join(lines))
    first_exception = reports[0].exc_info
    assert first_exception is not None
    raise error from first_exception[1]


def _commit_generated_tasks(session: Session, generated_tasks: list[PTask]) -> None:
    """Atomically commit generated tasks and the corresponding execution state."""
    previous_tasks = session.tasks
    session.tasks = [*previous_tasks, *generated_tasks]
    try:
        session.hook.pytask_collect_modify_tasks(session=session, tasks=session.tasks)
        dag = create_dag_from_session(session)
        scheduler = (
            session.scheduler.rebuild(dag) if session.scheduler is not None else None
        )
    except BaseException:
        session.tasks = previous_tasks
        raise

    previous_tasks[:] = session.tasks
    session.tasks = previous_tasks
    session.dag = dag
    session.scheduler = scheduler


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
