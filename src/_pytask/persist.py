"""Implement the ability for tasks to persist."""
import click
from _pytask.config import hookimpl
from _pytask.dag import node_and_neighbors
from _pytask.enums import ColorCode
from _pytask.exceptions import NodeNotFoundError
from _pytask.mark import get_specific_markers_from_task
from _pytask.outcomes import Persisted


@hookimpl
def pytask_parse_config(config):
    """Add the marker to the configuration."""
    config["markers"]["persist"] = (
        "Prevent execution of a task if all products exist and even if something has "
        "changed (dependencies, source file, products). This decorator might be useful "
        "for expensive tasks where only the formatting of the file has changed. The "
        "state of the files which have changed will also be remembered and another run "
        "will skip the task with success."
    )


@hookimpl
def pytask_execute_task_setup(session, task):
    """Exit persisting tasks early.

    The decorator needs to be set and all nodes need to exist.

    """
    if get_specific_markers_from_task(task, "persist"):
        try:
            for name in node_and_neighbors(session.dag, task.name):
                node = (
                    session.dag.nodes[name].get("task")
                    or session.dag.nodes[name]["node"]
                )
                node.state()
        except NodeNotFoundError:
            all_nodes_exist = False
        else:
            all_nodes_exist = True

        if all_nodes_exist:
            raise Persisted


@hookimpl
def pytask_execute_task_process_report(report):
    """Set task status to success.

    Do not return ``True`` so that states will be updated in database.

    """
    if report.exc_info and isinstance(report.exc_info[1], Persisted):
        report.success = True


@hookimpl
def pytask_execute_task_log_end(report):
    """Log a persisting task with a green p."""
    if report.success:
        if report.exc_info:
            if isinstance(report.exc_info[1], Persisted):
                click.secho("p", fg=ColorCode.SUCCESS, nl=False)
                return True
