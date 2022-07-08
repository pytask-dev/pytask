"""This module contains hook implementations concerning the execution."""
from __future__ import annotations

import inspect
import sys
import time
from typing import Any

from _pytask.config import hookimpl
from _pytask.config_utils import ShowCapture
from _pytask.console import console
from _pytask.console import create_summary_panel
from _pytask.console import create_url_style_for_task
from _pytask.console import format_strings_as_flat_tree
from _pytask.console import format_task_id
from _pytask.console import unify_styles
from _pytask.dag import descending_tasks
from _pytask.dag import TopologicalSorter
from _pytask.database import update_states_in_database
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark import Mark
from _pytask.mark_utils import has_mark
from _pytask.nodes import FilePathNode
from _pytask.nodes import Task
from _pytask.outcomes import count_outcomes
from _pytask.outcomes import Exit
from _pytask.outcomes import TaskOutcome
from _pytask.outcomes import WouldBeExecuted
from _pytask.report import ExecutionReport
from _pytask.session import Session
from _pytask.shared import get_first_non_none_value
from _pytask.shared import reduce_node_name
from _pytask.traceback import format_exception_without_traceback
from _pytask.traceback import remove_traceback_from_exc_info
from _pytask.traceback import render_exc_info
from pybaum.tree_util import tree_map
from rich.text import Text


@hookimpl
def pytask_parse_config(
    config: dict[str, Any],
    config_from_cli: dict[str, Any],
    config_from_file: dict[str, Any],
) -> None:
    """Parse the configuration."""
    config["show_errors_immediately"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="show_errors_immediately",
        default=False,
        callback=lambda x: x if x is None else bool(x),
    )


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Adjust the configuration after intermediate values have been parsed."""
    if config["show_errors_immediately"]:
        config["pm"].register(ShowErrorsImmediatelyPlugin)


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
def pytask_execute_task_protocol(session: Session, task: Task) -> ExecutionReport:
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
def pytask_execute_task_setup(session: Session, task: Task) -> None:
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

    would_be_executed = has_mark(task, "would_be_executed")
    if would_be_executed:
        raise WouldBeExecuted


@hookimpl(trylast=True)
def pytask_execute_task(session: Session, task: Task) -> bool:
    """Execute task."""
    if session.config["dry_run"]:
        raise WouldBeExecuted()
    else:
        kwargs = {**task.kwargs}

        func_arg_names = set(inspect.signature(task.function).parameters)
        for arg_name in ("depends_on", "produces"):
            if arg_name in func_arg_names:
                attribute = getattr(task, arg_name)
                kwargs[arg_name] = tree_map(lambda x: x.value, attribute)

        task.execute(**kwargs)
    return True


@hookimpl
def pytask_execute_task_teardown(session: Session, task: Task) -> None:
    """Check if :class:`_pytask.nodes.FilePathNode` are produced by a task."""
    missing_nodes = []
    for product in session.dag.successors(task.name):
        node = session.dag.nodes[product]["node"]
        if isinstance(node, FilePathNode):

            try:
                node.state()
            except NodeNotFoundError:
                missing_nodes.append(node)

    if missing_nodes:
        paths = [reduce_node_name(i, session.config["paths"]) for i in missing_nodes]
        formatted = format_strings_as_flat_tree(
            paths, "The task did not produce the following files:\n", ""
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
        update_states_in_database(session.dag, task.name)
    elif report.exc_info and isinstance(report.exc_info[1], WouldBeExecuted):
        report.outcome = TaskOutcome.WOULD_BE_EXECUTED

        for descending_task_name in descending_tasks(task.name, session.dag):
            descending_task = session.dag.nodes[descending_task_name]["task"]
            descending_task.markers.append(
                Mark(
                    "would_be_executed",
                    (),
                    {"reason": f"Previous task {task.name!r} would be executed."},
                )
            )
    else:
        for descending_task_name in descending_tasks(task.name, session.dag):
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

        if report.exc_info and isinstance(report.exc_info[1], Exit):
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
    @staticmethod
    @hookimpl(tryfirst=True)
    def pytask_execute_task_log_end(session: Session, report: ExecutionReport) -> None:
        if report.outcome == TaskOutcome.FAIL:
            _print_errored_task_report(session, report)


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
                and session.config["verbose"] >= 2
            ):
                _print_errored_task_report(session, report)

    console.rule(style="dim")

    panel = create_summary_panel(counts, TaskOutcome, "Collected tasks")
    console.print(panel)

    session.hook.pytask_log_session_footer(
        session=session,
        duration=session.execution_end - session.execution_start,
        outcome=TaskOutcome.FAIL if counts[TaskOutcome.FAIL] else TaskOutcome.SUCCESS,
    )

    if counts[TaskOutcome.FAIL]:
        raise ExecutionError

    return True


def _print_errored_task_report(session: Session, report: ExecutionReport) -> None:
    """Print the traceback and the exception of an errored report."""
    task_name = format_task_id(
        task=report.task,
        editor_url_scheme=session.config["editor_url_scheme"],
        short_name=True,
    )
    text = Text.assemble("Task ", task_name, " failed", style="failed")
    console.rule(text, style=report.outcome.style)

    console.print()

    if report.exc_info and isinstance(report.exc_info[1], Exit):
        console.print(format_exception_without_traceback(report.exc_info))
    else:
        console.print(render_exc_info(*report.exc_info, session.config["show_locals"]))

    console.print()
    show_capture = session.config["show_capture"]
    for when, key, content in report.sections:
        if key in ("stdout", "stderr") and show_capture in (
            ShowCapture[key.upper()],
            ShowCapture.ALL,
        ):
            console.rule(f"Captured {key} during {when}", style=None)
            console.print(content)
