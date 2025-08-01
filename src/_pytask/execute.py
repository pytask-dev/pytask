"""Contains hook implementations concerning the execution."""

from __future__ import annotations

import inspect
import sys
import time
from typing import TYPE_CHECKING
from typing import Any

from rich.text import Text

from _pytask.config import IS_FILE_SYSTEM_CASE_SENSITIVE
from _pytask.console import console
from _pytask.console import create_summary_panel
from _pytask.console import create_url_style_for_task
from _pytask.console import format_node_name
from _pytask.console import format_strings_as_flat_tree
from _pytask.console import unify_styles
from _pytask.dag_utils import TopologicalSorter
from _pytask.dag_utils import descending_tasks
from _pytask.dag_utils import node_and_neighbors
from _pytask.database_utils import has_node_changed
from _pytask.database_utils import update_states_in_database
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import NodeLoadError
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark import Mark
from _pytask.mark_utils import has_mark
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import PTask
from _pytask.nodes import DirectoryNode
from _pytask.outcomes import Exit
from _pytask.outcomes import SkippedUnchanged
from _pytask.outcomes import TaskOutcome
from _pytask.outcomes import WouldBeExecuted
from _pytask.outcomes import count_outcomes
from _pytask.pluginmanager import hookimpl
from _pytask.provisional_utils import collect_provisional_products
from _pytask.reports import ExecutionReport
from _pytask.traceback import remove_traceback_from_exc_info
from _pytask.tree_util import tree_leaves
from _pytask.tree_util import tree_map
from _pytask.tree_util import tree_structure
from _pytask.typing import is_task_generator

if TYPE_CHECKING:
    from _pytask.session import Session


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Adjust the configuration after intermediate values have been parsed."""
    if config["show_errors_immediately"]:
        config["pm"].register(ShowErrorsImmediatelyPlugin)


@hookimpl
def pytask_execute(session: Session) -> None:
    """Execute tasks."""
    session.hook.pytask_execute_log_start(session=session)
    session.scheduler = TopologicalSorter.from_dag(session.dag)
    session.hook.pytask_execute_build(session=session)
    session.hook.pytask_execute_log_end(
        session=session, reports=session.execution_reports
    )


@hookimpl
def pytask_execute_log_start(session: Session) -> None:
    """Start logging."""
    session.execution_start = time.time()

    # New line to separate note on collected items from task statuses.
    console.print()


@hookimpl
def pytask_execute_build(session: Session) -> bool | None:
    """Execute tasks."""
    if isinstance(session.scheduler, TopologicalSorter):
        while session.scheduler.is_active():
            task_name = session.scheduler.get_ready()[0]
            task = session.dag.nodes[task_name]["task"]
            report = session.hook.pytask_execute_task_protocol(
                session=session, task=task
            )
            session.execution_reports.append(report)
            session.scheduler.done(task_name)

            if session.should_stop:
                return True
        return True
    return None


@hookimpl
def pytask_execute_task_protocol(session: Session, task: PTask) -> ExecutionReport:
    """Follow the protocol to execute each task."""
    session.hook.pytask_execute_task_log_start(session=session, task=task)
    try:
        session.hook.pytask_execute_task_setup(session=session, task=task)
        session.hook.pytask_execute_task(session=session, task=task)
        session.hook.pytask_execute_task_teardown(session=session, task=task)
    except KeyboardInterrupt:  # pragma: no cover
        short_exc_info = remove_traceback_from_exc_info(sys.exc_info())
        report = ExecutionReport.from_task_and_exception(task, short_exc_info)
        session.should_stop = True
    except Exception:  # noqa: BLE001
        report = ExecutionReport.from_task_and_exception(task, sys.exc_info())
    else:
        report = ExecutionReport.from_task(task)
    session.hook.pytask_execute_task_process_report(session=session, report=report)
    session.hook.pytask_execute_task_log_end(session=session, task=task, report=report)

    return report


@hookimpl(trylast=True)
def pytask_execute_task_setup(session: Session, task: PTask) -> None:  # noqa: C901
    """Set up the execution of a task.

    1. Check whether all dependencies of a task are available.
    2. Create the directory where the product will be placed.

    """
    if has_mark(task, "would_be_executed"):
        raise WouldBeExecuted

    dag = session.dag

    # Task generators are always executed since their states are not updated, but we
    # skip the checks as well.
    needs_to_be_executed = session.config["force"] or is_task_generator(task)

    if not needs_to_be_executed:
        predecessors = set(dag.predecessors(task.signature)) | {task.signature}
        for node_signature in node_and_neighbors(dag, task.signature):
            node = dag.nodes[node_signature].get("task") or dag.nodes[
                node_signature
            ].get("node")

            # Skip provisional nodes that are products since they do not have a state.
            if node_signature not in predecessors and isinstance(
                node, PProvisionalNode
            ):
                continue

            node_state = node.state()

            if node_signature in predecessors and not node_state:
                msg = f"{task.name!r} requires missing node {node.name!r}."
                if IS_FILE_SYSTEM_CASE_SENSITIVE:
                    msg += (
                        "\n\n(Hint: Your file-system is case-sensitive. Check the "
                        "paths' capitalization carefully.)"
                    )
                raise NodeNotFoundError(msg)

            has_changed = has_node_changed(task=task, node=node, state=node_state)
            if has_changed:
                needs_to_be_executed = True

    if not needs_to_be_executed:
        collect_provisional_products(session, task)
        raise SkippedUnchanged

    # Create directory for product if it does not exist. Maybe this should be a `setup`
    # method for the node classes.
    for product in dag.successors(task.signature):
        node = dag.nodes[product]["node"]
        if isinstance(node, PPathNode):
            node.path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(node, DirectoryNode) and node.root_dir:
            node.root_dir.mkdir(parents=True, exist_ok=True)


def _safe_load(node: PNode | PProvisionalNode, task: PTask, *, is_product: bool) -> Any:
    try:
        return node.load(is_product=is_product)
    except Exception as e:
        msg = f"Exception while loading node {node.name!r} of task {task.name!r}"
        raise NodeLoadError(msg) from e


@hookimpl(trylast=True)
def pytask_execute_task(session: Session, task: PTask) -> bool:
    """Execute task."""
    if session.config["dry_run"]:
        raise WouldBeExecuted

    parameters = inspect.signature(task.function).parameters

    kwargs = {}
    for name, value in task.depends_on.items():
        kwargs[name] = tree_map(lambda x: _safe_load(x, task, is_product=False), value)

    for name, value in task.produces.items():
        if name in parameters:
            kwargs[name] = tree_map(
                lambda x: _safe_load(x, task, is_product=True), value
            )

    out = task.execute(**kwargs)

    if "return" in task.produces:
        structure_out = tree_structure(out)
        structure_return = tree_structure(task.produces["return"])

        # strict must be false when none is leaf.
        if not structure_return.is_prefix(structure_out, strict=False):
            msg = (
                f"The structure of the return annotation is not a subtree of the "
                f"structure of the function return.\n\nFunction return: {structure_out}"
                f"\n\nReturn annotation: {structure_return}"
            )
            raise ValueError(msg)

        nodes = tree_leaves(task.produces["return"])
        values = structure_return.flatten_up_to(out)
        for node, value in zip(nodes, values):
            if not isinstance(node, PProvisionalNode):
                node.save(value)

    return True


@hookimpl(trylast=True)
def pytask_execute_task_teardown(session: Session, task: PTask) -> None:
    """Check if nodes are produced by a task."""
    if is_task_generator(task):
        return

    collect_provisional_products(session, task)
    missing_nodes = [node for node in tree_leaves(task.produces) if not node.state()]
    if missing_nodes:
        paths = session.config["paths"]
        files = [format_node_name(i, paths).plain for i in missing_nodes]
        formatted = format_strings_as_flat_tree(
            files, "The task did not produce the following files:\n"
        )
        raise NodeNotFoundError(formatted)


@hookimpl(trylast=True)
def pytask_execute_task_process_report(
    session: Session, report: ExecutionReport
) -> bool:
    """Process the execution report of a task.

    If a task failed, skip all subsequent tasks. Else, update the states of related
    nodes in the database.

    """
    task = report.task
    if report.outcome == TaskOutcome.SUCCESS:
        update_states_in_database(session, task.signature)
    elif report.exc_info and isinstance(report.exc_info[1], WouldBeExecuted):
        report.outcome = TaskOutcome.WOULD_BE_EXECUTED

        for descending_task_name in descending_tasks(task.signature, session.dag):
            descending_task = session.dag.nodes[descending_task_name]["task"]
            descending_task.markers.append(
                Mark(
                    "would_be_executed",
                    (),
                    {"reason": f"Previous task {task.name!r} would be executed."},
                )
            )
    else:
        for descending_task_name in descending_tasks(task.signature, session.dag):
            descending_task = session.dag.nodes[descending_task_name]["task"]
            descending_task.markers.append(
                Mark(
                    "skip_ancestor_failed",
                    (),
                    {"reason": f"Previous task {task.name!r} failed."},
                )
            )

        session.n_tasks_failed += 1
        if session.n_tasks_failed >= session.config["max_failures"]:
            session.should_stop = True

        if report.exc_info and isinstance(report.exc_info[1], Exit):  # pragma: no cover
            session.should_stop = True

    return True


@hookimpl(trylast=True)
def pytask_execute_task_log_end(session: Session, report: ExecutionReport) -> None:
    """Log task outcome."""
    url_style = create_url_style_for_task(
        report.task.function, session.config["editor_url_scheme"]
    )
    console.print(
        report.outcome.symbol,
        style=unify_styles(report.outcome.style, url_style),
        end="",
    )


class ShowErrorsImmediatelyPlugin:
    """Namespace for plugin to show errors immediately after the execution."""

    @staticmethod
    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_end(report: ExecutionReport) -> None:
        """Print the error report of a task."""
        if report.outcome == TaskOutcome.FAIL:
            console.print(report)


@hookimpl
def pytask_execute_log_end(session: Session, reports: list[ExecutionReport]) -> bool:
    """Log information on the execution."""
    session.execution_end = time.time()

    counts = count_outcomes(reports, TaskOutcome)

    if session.config["show_traceback"]:
        console.print()
        if counts[TaskOutcome.FAIL]:
            console.rule(
                Text("Failures", style=TaskOutcome.FAIL.style),
                style=TaskOutcome.FAIL.style,
            )
            console.print()

        for report in reports:
            if report.outcome == TaskOutcome.FAIL or (
                report.outcome == TaskOutcome.SKIP_PREVIOUS_FAILED
                and session.config["verbose"] >= 2  # noqa: PLR2004
            ):
                console.print(report)

    console.rule(style="dim")

    description_total = "Collected task" if len(reports) == 1 else "Collected tasks"
    panel = create_summary_panel(counts, TaskOutcome, description_total)
    console.print(panel)

    session.hook.pytask_log_session_footer(
        session=session,
        duration=session.execution_end - session.execution_start,
        outcome=TaskOutcome.FAIL if counts[TaskOutcome.FAIL] else TaskOutcome.SUCCESS,
    )

    if counts[TaskOutcome.FAIL]:
        raise ExecutionError

    return True
