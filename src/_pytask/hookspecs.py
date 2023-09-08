"""Implement hook specifications or entry-points for pytask.

At each of the entry-points, a plugin can register a hook implementation which receives
the message send by the host and may send a response.

"""
from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

import pluggy


if TYPE_CHECKING:
    from _pytask.node_protocols import MetaNode
    from _pytask.models import NodeInfo
    from _pytask.node_protocols import PNode
    import click
    from _pytask.node_protocols import PTask
    import networkx as nx
    from pathlib import Path
    from _pytask.session import Session
    from _pytask.outcomes import CollectionOutcome
    from _pytask.outcomes import TaskOutcome
    from _pytask.reports import CollectionReport
    from _pytask.reports import ExecutionReport
    from _pytask.reports import DagReport


hookspec = pluggy.HookspecMarker("pytask")


@hookspec
def pytask_add_hooks(pm: pluggy.PluginManager) -> None:
    """Add hook specifications and implementations to the plugin manager.

    This hook is the first to be called to let plugins register their hook
    specifications and implementations.

    If you want to register plugins dynamically depending on the configuration, use
    :func:`pytask_post_parse` instead. See :mod:`_pytask.debugging` for an example.

    """


# Hooks for the command-line interface.


@hookspec
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the command line interface.

    The hook can be used to extend the command line interface either by providing new
    commands or adding options and arguments to existing commands.

    - Add commands via ``cli.add_command``.
    - Add options and arguments by extending ``cli.params`` or
      ``cli.commands["<name>"].params`` if the parameters only apply to a certain
      command.

    """


# Hooks for the configuration.


@hookspec(firstresult=True)
def pytask_configure(
    pm: pluggy.PluginManager, raw_config: dict[str, Any]
) -> dict[str, Any]:
    """Configure pytask.

    The main hook implementation which controls the configuration and calls subordinated
    hooks.

    """


@hookspec
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse configuration that is from CLI or file."""


@hookspec
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Post parsing.

    This hook allows to consolidate the configuration in case some plugins might be
    mutually exclusive. For example, the parallel execution provided by pytask-parallel
    does not work with any form of debugging. If debugging is turned on, parallelization
    can be turned of in this step.

    """


@hookspec
def pytask_unconfigure(session: Session) -> None:
    """Unconfigure a pytask session before the process is exited.

    The hook allows to return resources previously borrowed like :func:`pdb.set_trace`
    by :class:`_pytask.debugging.PytaskPDB` and do other stuff at the end of a session.

    """


# Hooks for the collection.


@hookspec(firstresult=True)
def pytask_collect(session: Session) -> Any:
    """Collect tasks from paths.

    The main hook implementation which controls the collection and calls subordinated
    hooks.

    """


@hookspec(firstresult=True)
def pytask_ignore_collect(path: Path, config: dict[str, Any]) -> bool:
    """Ignore collected path.

    This hook is indicates for each directory and file whether it should be ignored.
    This speeds up the collection.

    """


@hookspec
def pytask_collect_modify_tasks(session: Session, tasks: list[PTask]) -> None:
    """Modify tasks after they have been collected.

    This hook can be used to deselect tasks when they match a certain keyword or mark.

    """


@hookspec(firstresult=True)
def pytask_collect_file_protocol(
    session: Session, path: Path, reports: list[CollectionReport]
) -> list[CollectionReport]:
    """Start protocol to collect files.

    The protocol calls the subordinate hook :func:`pytask_collect_file` which might
    error if the file has a :class:`SyntaxError`.

    """


@hookspec
def pytask_collect_file(
    session: Session, path: Path, reports: list[CollectionReport]
) -> list[CollectionReport] | None:
    """Collect tasks from a file.

    If you want to collect tasks from other files, modify this hook.

    """


@hookspec
def pytask_collect_file_log(session: Session, reports: list[CollectionReport]) -> None:
    """Perform logging at the end of collecting a file."""


@hookspec(firstresult=True)
def pytask_collect_task_protocol(
    session: Session, path: Path | None, name: str, obj: Any
) -> CollectionReport | None:
    """Start protocol to collect tasks."""


@hookspec
def pytask_collect_task_setup(
    session: Session, path: Path | None, name: str, obj: Any
) -> None:
    """Steps before collecting a task."""


@hookspec(firstresult=True)
def pytask_collect_task(
    session: Session, path: Path | None, name: str, obj: Any
) -> PTask:
    """Collect a single task."""


@hookspec
def pytask_collect_task_teardown(session: Session, task: PTask) -> None:
    """Perform tear-down operations when a task was collected.

    Use this hook specification to, for example, perform checks on the collected task.

    """


@hookspec(firstresult=True)
def pytask_collect_node(
    session: Session, path: Path, node_info: NodeInfo
) -> PNode | None:
    """Collect a node which is a dependency or a product of a task."""


@hookspec(firstresult=True)
def pytask_collect_log(
    session: Session, reports: list[CollectionReport], tasks: list[PTask]
) -> None:
    """Log errors occurring during the collection.

    This hook reports errors during the collection.

    """


# Hooks for resolving dependencies.


@hookspec(firstresult=True)
def pytask_dag(session: Session) -> None:
    """Create a DAG.

    The main hook implementation which controls the resolution of dependencies and calls
    subordinated hooks.

    """


@hookspec(firstresult=True)
def pytask_dag_create_dag(session: Session, tasks: list[PTask]) -> nx.DiGraph:
    """Create the DAG.

    This hook creates the DAG from tasks, dependencies and products. The DAG can be used
    by a scheduler to find an execution order.

    """


@hookspec
def pytask_dag_modify_dag(session: Session, dag: nx.DiGraph) -> None:
    """Modify the DAG.

    This hook allows to make some changes to the DAG before it is validated and tasks
    are selected.

    """


@hookspec(firstresult=True)
def pytask_dag_validate_dag(session: Session, dag: nx.DiGraph) -> None:
    """Validate the DAG.

    This hook validates the DAG. For example, there can be cycles in the DAG if tasks,
    dependencies and products have been misspecified.

    """


@hookspec
def pytask_dag_select_execution_dag(session: Session, dag: nx.DiGraph) -> None:
    """Select the subgraph which needs to be executed.

    This hook determines which of the tasks have to be re-run because something has
    changed.

    """


@hookspec(firstresult=True)
def pytask_dag_has_node_changed(
    session: Session, dag: nx.DiGraph, node: MetaNode, task_name: str
) -> None:
    """Select the subgraph which needs to be executed.

    This hook determines which of the tasks have to be re-run because something has
    changed.

    """


@hookspec
def pytask_dag_log(session: Session, report: DagReport) -> None:
    """Log errors during resolving dependencies."""


# Hooks for running tasks.


@hookspec(firstresult=True)
def pytask_execute(session: Session) -> Any | None:
    """Loop over all tasks for the execution.

    The main hook implementation which controls the execution and calls subordinated
    hooks.

    """


@hookspec
def pytask_execute_log_start(session: Session) -> None:
    """Start logging of execution.

    This hook allows to provide a header with information before the execution starts.

    """


@hookspec(firstresult=True)
def pytask_execute_create_scheduler(session: Session) -> Any:
    """Create a scheduler for the execution.

    The scheduler provides information on which tasks are able to be executed. Its
    foundation is likely a topological ordering of the tasks based on the DAG.

    """


@hookspec(firstresult=True)
def pytask_execute_build(session: Session) -> Any:
    """Execute the build.

    This hook implements the main loop to execute tasks.

    """


@hookspec(firstresult=True)
def pytask_execute_task_protocol(session: Session, task: PTask) -> ExecutionReport:
    """Run the protocol for executing a test.

    This hook runs all stages of the execution process, setup, execution, and teardown
    and catches any exception.

    Then, the exception or success is stored in a report and logged.

    """


@hookspec(firstresult=True)
def pytask_execute_task_log_start(session: Session, task: PTask) -> None:
    """Start logging of task execution.

    This hook can be used to provide more verbose output during the execution.

    """


@hookspec
def pytask_execute_task_setup(session: Session, task: PTask) -> None:
    """Set up the task execution.

    This hook is called before the task is executed and can provide an entry-point to
    fast-fail a task. For example, raise and exception if a dependency is missing
    instead of letting the error occur in the execution.

    """


@hookspec(firstresult=True)
def pytask_execute_task(session: Session, task: PTask) -> Any:
    """Execute a task."""


@hookspec
def pytask_execute_task_teardown(session: Session, task: PTask) -> None:
    """Tear down task execution.

    This hook is executed after the task has been executed. It allows to perform clean-
    up operations or checks for missing products.

    """


@hookspec(firstresult=True)
def pytask_execute_task_process_report(
    session: Session, report: ExecutionReport
) -> Any | None:
    """Process the report of a task.

    This hook allows to process each report generated by a task which is either based on
    an exception or a success. Set the color and the symbol for logging.

    Some exceptions are intentionally raised like skips, but they should not be reported
    as failures.

    """


@hookspec(firstresult=True)
def pytask_execute_task_log_end(session: Session, report: ExecutionReport) -> None:
    """Log the end of a task execution."""


@hookspec
def pytask_execute_log_end(session: Session, reports: list[ExecutionReport]) -> None:
    """Log the footer of the execution report."""


# Hooks for general logging.


@hookspec
def pytask_log_session_header(session: Session) -> None:
    """Log session information at the begin of a run."""


@hookspec
def pytask_log_session_footer(
    session: Session,
    duration: float,
    outcome: CollectionOutcome | TaskOutcome,
) -> None:
    """Log session information at the end of a run."""


# Hooks for profile.


@hookspec
def pytask_profile_add_info_on_task(
    session: Session, tasks: list[PTask], profile: dict[str, dict[Any, Any]]
) -> None:
    """Add information on task for profile.

    Hook implementations can add information to the ``profile`` dictionary. The
    dictionary's keys are the task names. The value for each task is a dictionary itself
    where keys correspond to columns of the profile table.

    """


@hookspec
def pytask_profile_export_profile(
    session: Session, profile: dict[str, dict[Any, Any]]
) -> None:
    """Export the profile."""
