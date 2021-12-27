import sys
import time
from typing import Any
from typing import Dict
from typing import List

import networkx as nx
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import create_url_style_for_task
from _pytask.console import theme
from _pytask.console import unify_styles
from _pytask.dag import descending_tasks
from _pytask.dag import node_and_neighbors
from _pytask.dag import TopologicalSorter
from _pytask.database import create_or_update_state
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark import Mark
from _pytask.nodes import FilePathNode
from _pytask.nodes import MetaTask
from _pytask.outcomes import Exit
from _pytask.outcomes import Persisted
from _pytask.outcomes import Skipped
from _pytask.report import ExecutionReport
from _pytask.session import Session
from _pytask.shared import get_first_non_none_value
from _pytask.shared import reduce_node_name
from _pytask.traceback import format_exception_without_traceback
from _pytask.traceback import remove_traceback_from_exc_info
from _pytask.traceback import render_exc_info
from rich.text import Text


@hookimpl
def pytask_post_parse(config: Dict[str, Any]) -> None:
    if config["show_errors_immediately"]:
        config["pm"].register(ShowErrorsImmediatelyPlugin)


@hookimpl
def pytask_parse_config(
    config: Dict[str, Any],
    config_from_cli: Dict[str, Any],
    config_from_file: Dict[str, Any],
) -> None:
    config["show_errors_immediately"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="show_errors_immediately",
        default=False,
        callback=lambda x: x if x is None else bool(x),
    )


@hookimpl
def pytask_execute(session: Session) -> None:
    """Execute tasks."""
    session.hook.pytask_execute_log_start(session=session)
    session.scheduler = session.hook.pytask_execute_create_scheduler(session=session)
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


@hookimpl(trylast=True)
def pytask_execute_create_scheduler(session: Session) -> TopologicalSorter:
    """Create a scheduler based on topological sorting."""
    scheduler = TopologicalSorter.from_dag(session.dag)
    scheduler.prepare()
    return scheduler


@hookimpl
def pytask_execute_build(session: Session) -> bool:
    """Execute tasks."""
    if isinstance(session.scheduler, TopologicalSorter):
        for name in session.scheduler.static_order():
            task = session.dag.nodes[name]["task"]
            report = session.hook.pytask_execute_task_protocol(
                session=session, task=task
            )
            session.execution_reports.append(report)

            if session.should_stop:
                return True
        return True
    else:
        return None


@hookimpl
def pytask_execute_task_protocol(session: Session, task: MetaTask) -> ExecutionReport:
    """Follow the protocol to execute each task."""
    session.hook.pytask_execute_task_log_start(session=session, task=task)
    try:
        session.hook.pytask_execute_task_setup(session=session, task=task)
        session.hook.pytask_execute_task(session=session, task=task)
        session.hook.pytask_execute_task_teardown(session=session, task=task)
    except KeyboardInterrupt:
        short_exc_info = remove_traceback_from_exc_info(sys.exc_info())
        report = ExecutionReport.from_task_and_exception(task, short_exc_info)
        session.should_stop = True
    except Exception:
        report = ExecutionReport.from_task_and_exception(task, sys.exc_info())
    else:
        report = ExecutionReport.from_task(task)
    session.hook.pytask_execute_task_process_report(session=session, report=report)
    session.hook.pytask_execute_task_log_end(session=session, task=task, report=report)

    return report


@hookimpl(trylast=True)
def pytask_execute_task_setup(session: Session, task: MetaTask) -> None:
    """Set up the execution of a task.

    1. Check whether all dependencies of a task are available.
    2. Create the directory where the product will be placed.

    """
    for dependency in session.dag.predecessors(task.name):
        node = session.dag.nodes[dependency]["node"]
        try:
            node.state()
        except NodeNotFoundError as e:
            raise NodeNotFoundError(
                f"{node.name} is missing and required for {task.name}."
            ) from e

    # Create directory for product if it does not exist. Maybe this should be a `setup`
    # method for the node classes.
    for product in session.dag.successors(task.name):
        node = session.dag.nodes[product]["node"]
        if isinstance(node, FilePathNode):
            node.path.parent.mkdir(parents=True, exist_ok=True)


@hookimpl
def pytask_execute_task(task: MetaTask) -> None:
    """Execute task."""
    task.execute()


@hookimpl
def pytask_execute_task_teardown(session: Session, task: MetaTask) -> None:
    """Check if each produced node was indeed produced."""
    for product in session.dag.successors(task.name):
        node = session.dag.nodes[product]["node"]
        try:
            node.state()
        except NodeNotFoundError as e:
            raise NodeNotFoundError(
                f"{node.name} was not produced by {task.name}."
            ) from e


@hookimpl(trylast=True)
def pytask_execute_task_process_report(
    session: Session, report: ExecutionReport
) -> bool:
    """Process the execution report of a task.

    If a task failed, skip all subsequent tasks. Else, update the states of related
    nodes in the database.

    """
    task = report.task
    if report.success:
        _update_states_in_database(session.dag, task.name)
        report.symbol = "."
        report.style = theme.styles["success"]
    else:
        report.symbol = "F"
        report.style = theme.styles["failed"]
        for descending_task_name in descending_tasks(task.name, session.dag):
            descending_task = session.dag.nodes[descending_task_name]["task"]
            descending_task.markers.append(
                Mark(
                    "skip_ancestor_failed",
                    (),
                    {"reason": f"Previous task '{task.name}' failed."},
                )
            )

        session.n_tasks_failed += 1
        if session.n_tasks_failed >= session.config["max_failures"]:
            session.should_stop = True

        if report.exc_info and isinstance(report.exc_info[1], Exit):
            session.should_stop = True

    return True


@hookimpl(trylast=True)
def pytask_execute_task_log_end(session: Session, report: ExecutionReport) -> None:
    """Log task outcome."""
    url_style = create_url_style_for_task(
        report.task, session.config["editor_url_scheme"]
    )
    console.print(report.symbol, style=unify_styles(report.style, url_style), end="")


class ShowErrorsImmediatelyPlugin:
    @staticmethod
    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_end(session: Session, report: ExecutionReport) -> None:
        if not report.success:
            _print_errored_task_report(session, report)


@hookimpl
def pytask_execute_log_end(session: Session, reports: List[ExecutionReport]) -> bool:
    session.execution_end = time.time()

    n_failed = len(reports) - sum(report.success for report in reports)
    n_skipped = sum(
        isinstance(report.exc_info[1], Skipped) for report in reports if report.exc_info
    )
    n_persisted = sum(
        isinstance(report.exc_info[1], Persisted)
        for report in reports
        if report.exc_info
    )
    n_successful = len(reports) - n_failed - n_skipped - n_persisted

    console.print()
    if n_failed:
        console.rule(Text("Failures", style="failed"), style="failed")
        console.print()

    for report in reports:
        if not report.success:
            _print_errored_task_report(session, report)

    session.hook.pytask_log_session_footer(
        session=session,
        infos=[
            (n_successful, "succeeded", theme.styles["success"]),
            (n_persisted, "persisted", theme.styles["success"]),
            (n_failed, "failed", theme.styles["failed"]),
            (n_skipped, "skipped", theme.styles["skipped"]),
        ],
        duration=round(session.execution_end - session.execution_start, 2),
        style=theme.styles["failed"] if n_failed else theme.styles["success"],
    )

    if n_failed:
        raise ExecutionError

    return True


def _print_errored_task_report(session: Session, report: ExecutionReport) -> None:
    """Print the traceback and the exception of an errored report."""
    task_name = reduce_node_name(report.task, session.config["paths"])
    if len(task_name) > console.width - 15:
        task_name = report.task.base_name

    url_style = create_url_style_for_task(
        report.task, session.config["editor_url_scheme"]
    )

    console.rule(
        Text(f"Task {task_name} failed", style=unify_styles(report.style, url_style)),
        style=report.style,
    )

    console.print()

    if report.exc_info and isinstance(report.exc_info[1], Exit):
        console.print(format_exception_without_traceback(report.exc_info))
    else:
        console.print(render_exc_info(*report.exc_info, session.config["show_locals"]))

    console.print()
    show_capture = session.config["show_capture"]
    for when, key, content in report.sections:
        if key in ("stdout", "stderr") and show_capture in (key, "all"):
            console.rule(f"Captured {key} during {when}", style=None)
            console.print(content)


def _update_states_in_database(dag: nx.DiGraph, task_name: str) -> None:
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(dag, task_name):
        node = dag.nodes[name].get("task") or dag.nodes[name]["node"]
        create_or_update_state(task_name, node.name, node.state())
