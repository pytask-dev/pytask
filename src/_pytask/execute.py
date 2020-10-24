import sys
import time
import traceback

import click
from _pytask.config import hookimpl
from _pytask.dag import descending_tasks
from _pytask.dag import node_and_neighbors
from _pytask.dag import sort_tasks_topologically
from _pytask.database import create_or_update_state
from _pytask.enums import ColorCode
from _pytask.exceptions import ExecutionError
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark import Mark
from _pytask.nodes import FilePathNode
from _pytask.report import ExecutionReport
from _pytask.report import format_execute_footer


@hookimpl
def pytask_execute(session):
    """Execute tasks."""
    session.hook.pytask_execute_log_start(session=session)
    session.scheduler = session.hook.pytask_execute_create_scheduler(session=session)
    session.execution_reports = session.hook.pytask_execute_build(session=session)
    session.hook.pytask_execute_log_end(
        session=session, reports=session.execution_reports
    )


@hookimpl
def pytask_execute_log_start(session):
    """Start logging."""
    session.execution_start = time.time()

    # New line to separate note on collected items from task statuses.
    click.echo("")


@hookimpl(trylast=True)
def pytask_execute_create_scheduler(session):
    """Create a scheduler based on topological sorting."""
    for node in sort_tasks_topologically(session.dag):
        task = session.dag.nodes[node]["task"]
        yield task


@hookimpl
def pytask_execute_build(session):
    """Execute tasks."""
    reports = []
    for task in session.scheduler:
        report = session.hook.pytask_execute_task_protocol(session=session, task=task)
        reports.append(report)

    return reports


@hookimpl
def pytask_execute_task_protocol(session, task):
    """Follow the protocol to execute each task."""
    session.hook.pytask_execute_task_log_start(session=session, task=task)
    try:
        session.hook.pytask_execute_task_setup(session=session, task=task)
        session.hook.pytask_execute_task(session=session, task=task)
        session.hook.pytask_execute_task_teardown(session=session, task=task)
    except Exception:
        report = ExecutionReport.from_task_and_exception(task, sys.exc_info())
    else:
        report = ExecutionReport.from_task(task)
    session.hook.pytask_execute_task_process_report(session=session, report=report)
    session.hook.pytask_execute_task_log_end(session=session, task=task, report=report)

    return report


@hookimpl(trylast=True)
def pytask_execute_task_setup(session, task):
    """Set up the execution of a task.

    1. Check whether all dependencies of a task are available.
    2. Create the directory where the product will be placed.

    """
    for dependency in session.dag.predecessors(task.name):
        node = session.dag.nodes[dependency]["node"]
        try:
            node.state()
        except NodeNotFoundError:
            raise NodeNotFoundError(
                f"{node.name} is missing and required for {task.name}."
            )

    # Create directory for product if it does not exist. Maybe this should be a `setup`
    # method for the node classes.
    for product in session.dag.successors(task.name):
        node = session.dag.nodes[product]["node"]
        if isinstance(node, FilePathNode):
            node.value.parent.mkdir(parents=True, exist_ok=True)


@hookimpl
def pytask_execute_task(task):
    """Execute task."""
    task.execute()


@hookimpl
def pytask_execute_task_teardown(session, task):
    """Check if each produced node was indeed produced."""
    for product in session.dag.successors(task.name):
        node = session.dag.nodes[product]["node"]
        try:
            node.state()
        except NodeNotFoundError:
            raise NodeNotFoundError(f"{node.name} was not produced by {task.name}.")


@hookimpl(trylast=True)
def pytask_execute_task_process_report(session, report):
    """Process the execution report of a task.

    If a task failed, skip all subsequent tasks. Else, update the states of related
    nodes in the database.

    """
    task = report.task
    if report.success:
        _update_states_in_database(session.dag, task.name)
    else:
        for descending_task_name in descending_tasks(task.name, session.dag):
            descending_task = session.dag.nodes[descending_task_name]["task"]
            descending_task.markers.append(
                Mark(
                    "skip_ancestor_failed",
                    (),
                    {"reason": f"Previous task '{task.name}' failed."},
                )
            )
    return True


@hookimpl(trylast=True)
def pytask_execute_task_log_end(report):
    """Log task outcome."""
    if report.success:
        click.secho(".", fg=ColorCode.SUCCESS.value, nl=False)
    else:
        click.secho("F", fg=ColorCode.FAILED.value, nl=False)

    return True


@hookimpl
def pytask_execute_log_end(session, reports):
    session.execution_end = time.time()

    n_successful = sum(report.success for report in reports)
    n_failed = len(reports) - n_successful
    tm_width = session.config["terminal_width"]

    click.echo("")
    any_failure = any(not report.success for report in reports)
    if any_failure:
        click.echo(f"{{:=^{tm_width}}}".format(" Failures "))

    for report in reports:
        if not report.success:

            message = f" Task {report.task.name} failed "
            if len(message) > tm_width:
                click.echo("_" * tm_width)
                click.echo(message)
            else:
                click.echo(f"{{:_^{tm_width}}}".format(message))

            click.echo("")

            traceback.print_exception(*report.exc_info)

            click.echo("")

            if session.config["capture"] != "no":
                for when, key, content in report.sections:
                    click.echo(
                        f"{{:-^{tm_width}}}".format(f" Captured {key} during {when} ")
                    )
                    click.echo(content)

    duration = round(session.execution_end - session.execution_start, 2)
    click.echo(
        format_execute_footer(n_successful, n_failed, duration, tm_width), nl=True
    )

    if n_failed:
        raise ExecutionError

    return True


def _update_states_in_database(dag, task_name):
    """Update the state for each node of a task in the database."""
    for name in node_and_neighbors(dag, task_name):
        node = dag.nodes[name].get("task") or dag.nodes[name]["node"]
        create_or_update_state(task_name, node.name, node.state())
