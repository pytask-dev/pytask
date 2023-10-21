"""Contains code related to resolving dependencies."""
from __future__ import annotations

import hashlib
import itertools
import sys
from typing import Sequence
from typing import TYPE_CHECKING

import networkx as nx
from _pytask.config import hookimpl
from _pytask.config import IS_FILE_SYSTEM_CASE_SENSITIVE
from _pytask.console import ARROW_DOWN_ICON
from _pytask.console import console
from _pytask.console import FILE_ICON
from _pytask.console import format_node_name
from _pytask.console import render_to_string
from _pytask.console import TASK_ICON
from _pytask.dag_utils import node_and_neighbors
from _pytask.dag_utils import task_and_descending_tasks
from _pytask.dag_utils import TopologicalSorter
from _pytask.database_utils import DatabaseSession
from _pytask.database_utils import State
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.mark import Mark
from _pytask.mark_utils import get_marks
from _pytask.mark_utils import has_mark
from _pytask.node_protocols import MetaNode
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.nodes import PythonNode
from _pytask.report import DagReport
from _pytask.shared import reduce_names_of_multiple_nodes
from _pytask.traceback import remove_internal_traceback_frames_from_exception
from _pytask.traceback import render_exc_info
from _pytask.tree_util import tree_map
from rich.text import Text
from rich.tree import Tree

if TYPE_CHECKING:
    from pathlib import Path
    from _pytask.session import Session


@hookimpl
def pytask_dag(session: Session) -> bool | None:
    """Create a directed acyclic graph (DAG) capturing dependencies between functions.

    Parameters
    ----------
    session : _pytask.session.Session
        Dictionary containing tasks.

    """
    try:
        session.dag = session.hook.pytask_dag_create_dag(
            session=session, tasks=session.tasks
        )
        session.hook.pytask_dag_modify_dag(session=session, dag=session.dag)
        session.hook.pytask_dag_validate_dag(session=session, dag=session.dag)
        session.hook.pytask_dag_select_execution_dag(session=session, dag=session.dag)

    except Exception:  # noqa: BLE001
        report = DagReport.from_exception(sys.exc_info())
        session.hook.pytask_dag_log(session=session, report=report)
        session.dag_reports = report

        raise ResolvingDependenciesError from None

    else:
        return True


@hookimpl
def pytask_dag_create_dag(tasks: list[PTask]) -> nx.DiGraph:
    """Create the DAG from tasks, dependencies and products."""

    def _add_dependency(dag: nx.DiGraph, task: PTask, node: PNode) -> None:
        """Add a dependency to the DAG."""
        dag.add_node(node.name, node=node)
        dag.add_edge(node.name, task.name)

        # If a node is a PythonNode wrapped in another PythonNode, it is a product from
        # another task that is a dependency in the current task. Thus, draw an edge
        # connecting the two nodes.
        if isinstance(node, PythonNode) and isinstance(node.value, PythonNode):
            dag.add_edge(node.value.name, node.name)

    def _add_product(dag: nx.DiGraph, task: PTask, node: PNode) -> None:
        """Add a product to the DAG."""
        dag.add_node(node.name, node=node)
        dag.add_edge(task.name, node.name)

    dag = nx.DiGraph()

    for task in tasks:
        dag.add_node(task.name, task=task)

        tree_map(lambda x: _add_dependency(dag, task, x), task.depends_on)
        tree_map(lambda x: _add_product(dag, task, x), task.produces)

        # If a node is a PythonNode wrapped in another PythonNode, it is a product from
        # another task that is a dependency in the current task. Thus, draw an edge
        # connecting the two nodes.
        tree_map(
            lambda x: dag.add_edge(x.value.name, x.name)
            if isinstance(x, PythonNode) and isinstance(x.value, PythonNode)
            else None,
            task.depends_on,
        )

    _check_if_dag_has_cycles(dag)

    return dag


@hookimpl
def pytask_dag_select_execution_dag(session: Session, dag: nx.DiGraph) -> None:
    """Select the tasks which need to be executed."""
    scheduler = TopologicalSorter.from_dag(dag)
    visited_nodes: set[str] = set()

    while scheduler.is_active():
        task_name = scheduler.get_ready()[0]
        if task_name not in visited_nodes:
            task = dag.nodes[task_name]["task"]
            have_changed = _have_task_or_neighbors_changed(session, dag, task)
            if have_changed:
                visited_nodes.update(task_and_descending_tasks(task_name, dag))
            else:
                dag.nodes[task_name]["task"].markers.append(
                    Mark("skip_unchanged", (), {})
                )
        scheduler.done(task_name)


@hookimpl
def pytask_dag_validate_dag(session: Session, dag: nx.DiGraph) -> None:
    """Validate the DAG."""
    _check_if_root_nodes_are_available(dag, session.config["paths"])
    _check_if_tasks_have_the_same_products(dag, session.config["paths"])


def _have_task_or_neighbors_changed(
    session: Session, dag: nx.DiGraph, task: PTask
) -> bool:
    """Indicate whether dependencies or products of a task have changed."""
    return any(
        session.hook.pytask_dag_has_node_changed(
            session=session,
            dag=dag,
            task_name=task.name,
            node=dag.nodes[node_name].get("task") or dag.nodes[node_name].get("node"),
        )
        for node_name in node_and_neighbors(dag, task.name)
    )


@hookimpl(trylast=True)
def pytask_dag_has_node_changed(node: MetaNode, task_name: str) -> bool:
    """Indicate whether a single dependency or product has changed."""
    # If node does not exist, we receive None.
    node_state = node.state()
    if node_state is None:
        return True

    with DatabaseSession() as session:
        db_state = session.get(State, (task_name, node.name))

    # If the node is not in the database.
    if db_state is None:
        return True

    if isinstance(node, (PPathNode, PTaskWithPath)):
        # If the modification times match, the node has not been changed.
        if node_state == db_state.modification_time:
            return False

        # If the modification time changed, quickly return for non-tasks.
        if not isinstance(node, PTaskWithPath):
            return True

        # When modification times changed, we are still comparing the hash of the file
        # to avoid unnecessary and expensive reexecutions of tasks.
        hash_ = hashlib.sha256(node.path.read_bytes()).hexdigest()
        return hash_ != db_state.hash_

    return node_state != db_state.hash_


def _check_if_dag_has_cycles(dag: nx.DiGraph) -> None:
    """Check if DAG has cycles."""
    try:
        cycles = nx.algorithms.cycles.find_cycle(dag)
    except nx.NetworkXNoCycle:
        pass
    else:
        msg = (
            f"The DAG contains cycles which means a dependency is directly or "
            "indirectly a product of the same task. See the following the path of "
            f"nodes in the graph which forms the cycle.\n\n{_format_cycles(cycles)}"
        )
        raise ResolvingDependenciesError(msg)


def _format_cycles(cycles: list[tuple[str, ...]]) -> str:
    """Format cycles as a paths connected by arrows."""
    chain = [x for i, x in enumerate(itertools.chain(*cycles)) if i % 2 == 0]
    chain += [cycles[-1][1]]

    lines = chain[:1]
    for x in chain[1:]:
        lines.extend(("     " + ARROW_DOWN_ICON, x))
    return "\n".join(lines)


_TEMPLATE_ERROR: str = (
    "Some dependencies do not exist or are not produced by any task. See the following "
    "tree which shows which dependencies are missing for which tasks.\n\n{}"
)
if IS_FILE_SYSTEM_CASE_SENSITIVE:
    _TEMPLATE_ERROR += (
        "\n\n(Hint: Your file-system is case-sensitive. Check the paths' "
        "capitalization carefully.)"
    )


def _check_if_root_nodes_are_available(dag: nx.DiGraph, paths: Sequence[Path]) -> None:
    __tracebackhide__ = True

    missing_root_nodes = []
    is_task_skipped: dict[str, bool] = {}

    for node in dag.nodes:
        is_node = "node" in dag.nodes[node]
        is_without_parents = len(list(dag.predecessors(node))) == 0
        if is_node and is_without_parents:
            are_all_tasks_skipped, is_task_skipped = _check_if_tasks_are_skipped(
                node, dag, is_task_skipped
            )
            if not are_all_tasks_skipped:
                try:
                    node_exists = dag.nodes[node]["node"].state()
                except Exception as e:  # noqa: BLE001
                    e = remove_internal_traceback_frames_from_exception(e)
                    msg = _format_exception_from_failed_node_state(node, dag)
                    raise ResolvingDependenciesError(msg) from e
                if not node_exists:
                    missing_root_nodes.append(node)

    if missing_root_nodes:
        dictionary = {}
        for node in missing_root_nodes:
            short_node_name = format_node_name(dag.nodes[node]["node"], paths).plain
            not_skipped_successors = [
                task for task in dag.successors(node) if not is_task_skipped[task]
            ]
            short_successors = reduce_names_of_multiple_nodes(
                not_skipped_successors, dag, paths
            )
            dictionary[short_node_name] = short_successors

        text = _format_dictionary_to_tree(dictionary, "Missing dependencies:")
        raise ResolvingDependenciesError(_TEMPLATE_ERROR.format(text)) from None


def _format_exception_from_failed_node_state(node_name: str, dag: nx.DiGraph) -> str:
    """Format message when ``node.state()`` threw an exception."""
    tasks = [dag.nodes[i]["task"] for i in dag.successors(node_name)]
    names = [getattr(x, "display_name", x.name) for x in tasks]
    successors = ", ".join([f"{name!r}" for name in names])
    return (
        f"While checking whether dependency {node_name!r} from task(s) "
        f"{successors} exists, an error was raised."
    )


def _check_if_tasks_are_skipped(
    node: PNode, dag: nx.DiGraph, is_task_skipped: dict[str, bool]
) -> tuple[bool, dict[str, bool]]:
    """Check for a given node whether it is only used by skipped tasks."""
    are_all_tasks_skipped = []
    for successor in dag.successors(node):
        if successor not in is_task_skipped:
            is_task_skipped[successor] = _check_if_task_is_skipped(successor, dag)
        are_all_tasks_skipped.append(is_task_skipped[successor])

    return all(are_all_tasks_skipped), is_task_skipped


def _check_if_task_is_skipped(task_name: str, dag: nx.DiGraph) -> bool:
    task = dag.nodes[task_name]["task"]
    is_skipped = has_mark(task, "skip")

    if is_skipped:
        return True

    skip_if_markers = get_marks(task, "skipif")
    return any(_skipif(*marker.args, **marker.kwargs)[0] for marker in skip_if_markers)


def _skipif(condition: bool, *, reason: str) -> tuple[bool, str]:
    """Shameless copy to circumvent circular imports."""
    return condition, reason


def _format_dictionary_to_tree(dict_: dict[str, list[str]], title: str) -> str:
    """Format missing root nodes."""
    tree = Tree(title)

    for node, tasks in dict_.items():
        branch = tree.add(Text.assemble(FILE_ICON, node))
        for task in tasks:
            branch.add(Text.assemble(TASK_ICON, task))

    return render_to_string(tree, console=console, strip_styles=True)


def _check_if_tasks_have_the_same_products(dag: nx.DiGraph, paths: list[Path]) -> None:
    nodes_created_by_multiple_tasks = []

    for node in dag.nodes:
        is_node = "node" in dag.nodes[node]
        if is_node:
            parents = list(dag.predecessors(node))
            if len(parents) > 1:
                nodes_created_by_multiple_tasks.append(node)

    if nodes_created_by_multiple_tasks:
        dictionary = {}
        for node in nodes_created_by_multiple_tasks:
            short_node_name = format_node_name(dag.nodes[node]["node"], paths).plain
            short_predecessors = reduce_names_of_multiple_nodes(
                dag.predecessors(node), dag, paths
            )
            dictionary[short_node_name] = short_predecessors
        text = _format_dictionary_to_tree(dictionary, "Products from multiple tasks:")
        msg = (
            f"There are some tasks which produce the same output. See the following "
            f"tree which shows which products are produced by multiple tasks.\n\n{text}"
        )
        raise ResolvingDependenciesError(msg)


@hookimpl
def pytask_dag_log(session: Session, report: DagReport) -> None:
    """Log errors which happened while resolving dependencies."""
    console.print()
    console.rule(
        Text("Failures during resolving dependencies", style="failed"),
        style="failed",
    )

    console.print()
    console.print(
        render_exc_info(*report.exc_info, show_locals=session.config["show_locals"])
    )

    console.print()
    console.rule(style="failed")
