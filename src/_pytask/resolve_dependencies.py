import itertools
import sys
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import networkx as nx
from _pytask.config import hookimpl
from _pytask.config import IS_FILE_SYSTEM_CASE_SENSITIVE
from _pytask.console import ARROW_DOWN_ICON
from _pytask.console import console
from _pytask.console import FILE_ICON
from _pytask.console import render_to_string
from _pytask.console import TASK_ICON
from _pytask.dag import node_and_neighbors
from _pytask.dag import task_and_descending_tasks
from _pytask.dag import TopologicalSorter
from _pytask.database import State
from _pytask.exceptions import NodeNotFoundError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.mark import Mark
from _pytask.mark_utils import get_specific_markers_from_task
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.path import find_common_ancestor_of_nodes
from _pytask.report import ResolvingDependenciesReport
from _pytask.session import Session
from _pytask.shared import reduce_names_of_multiple_nodes
from _pytask.shared import reduce_node_name
from _pytask.traceback import render_exc_info
from pony import orm
from rich.text import Text
from rich.tree import Tree


@hookimpl
def pytask_resolve_dependencies(session: Session) -> Optional[bool]:
    """Create a directed acyclic graph (DAG) capturing dependencies between functions.

    Parameters
    ----------
    session : _pytask.session.Session
        Dictionary containing tasks.

    """
    try:
        session.dag = session.hook.pytask_resolve_dependencies_create_dag(
            session=session, tasks=session.tasks
        )
        session.hook.pytask_resolve_dependencies_modify_dag(
            session=session, dag=session.dag
        )
        session.hook.pytask_resolve_dependencies_validate_dag(
            session=session, dag=session.dag
        )
        session.hook.pytask_resolve_dependencies_select_execution_dag(
            session=session, dag=session.dag
        )

    except Exception:
        report = ResolvingDependenciesReport.from_exception(sys.exc_info())
        session.hook.pytask_resolve_dependencies_log(session=session, report=report)
        session.resolving_dependencies_report = report

        raise ResolvingDependenciesError from None

    else:
        return True


@hookimpl
def pytask_resolve_dependencies_create_dag(tasks: List[MetaTask]) -> nx.DiGraph:
    """Create the DAG from tasks, dependencies and products."""
    dag = nx.DiGraph()

    for task in tasks:
        dag.add_node(task.name, task=task)

        for dependency in task.depends_on.values():
            dag.add_node(dependency.name, node=dependency)
            dag.add_edge(dependency.name, task.name)

        for product in task.produces.values():
            dag.add_node(product.name, node=product)
            dag.add_edge(task.name, product.name)

    _check_if_dag_has_cycles(dag)

    return dag


@hookimpl
def pytask_resolve_dependencies_select_execution_dag(dag: nx.DiGraph) -> None:
    """Select the tasks which need to be executed."""
    scheduler = TopologicalSorter.from_dag(dag)
    visited_nodes = []

    for task_name in scheduler.static_order():
        if task_name not in visited_nodes:
            have_changed = _have_task_or_neighbors_changed(task_name, dag)
            if have_changed:
                visited_nodes += list(task_and_descending_tasks(task_name, dag))
            else:
                dag.nodes[task_name]["task"].markers.append(
                    Mark("skip_unchanged", (), {})
                )


@hookimpl
def pytask_resolve_dependencies_validate_dag(dag: nx.DiGraph) -> None:
    """Validate the DAG."""
    _check_if_root_nodes_are_available(dag)
    _check_if_tasks_have_the_same_products(dag)


def _have_task_or_neighbors_changed(task_name: str, dag: nx.DiGraph) -> bool:
    """Indicate whether dependencies or products of a task have changed."""
    return any(
        _has_node_changed(task_name, dag.nodes[node])
        for node in node_and_neighbors(dag, task_name)
    )


@orm.db_session
def _has_node_changed(
    task_name: str, node_dict: Dict[str, Union[MetaNode, MetaTask]]
) -> bool:
    """Indicate whether a single dependency or product has changed."""
    node = node_dict.get("task") or node_dict["node"]
    try:
        state = node.state()
    except NodeNotFoundError:
        out = True
    else:
        try:
            state_in_db = State[task_name, node.name].state  # type: ignore
        except orm.ObjectNotFound:
            out = True
        else:
            out = state != state_in_db

    return out


def _check_if_dag_has_cycles(dag: nx.DiGraph) -> None:
    """Check if DAG has cycles."""
    try:
        cycles = nx.algorithms.cycles.find_cycle(dag)
    except nx.NetworkXNoCycle:
        pass
    else:
        raise ResolvingDependenciesError(
            "The DAG contains cycles which means a dependency is directly or "
            "indirectly a product of the same task. See the following the path of "
            "nodes in the graph which forms the cycle."
            f"\n\n{_format_cycles(cycles)}"
        )


def _format_cycles(cycles: List[Tuple[str, ...]]) -> str:
    """Format cycles as a paths connected by arrows."""
    chain = [x for i, x in enumerate(itertools.chain(*cycles)) if i % 2 == 0]
    chain += [cycles[-1][1]]

    lines = chain[:1]
    for x in chain[1:]:
        lines.append("     " + ARROW_DOWN_ICON)
        lines.append(x)
    text = "\n".join(lines)

    return text


_TEMPLATE_ERROR: str = (
    "Some dependencies do not exist or are not produced by any task. See the following "
    "tree which shows which dependencies are missing for which tasks.\n\n{}"
)
if IS_FILE_SYSTEM_CASE_SENSITIVE:
    _TEMPLATE_ERROR += "\n\n(Hint: Sometimes case sensitivity is at fault.)"


def _check_if_root_nodes_are_available(dag: nx.DiGraph) -> None:
    missing_root_nodes = []
    is_task_skipped: Dict[str, bool] = {}

    for node in dag.nodes:
        is_node = "node" in dag.nodes[node]
        is_without_parents = len(list(dag.predecessors(node))) == 0
        if is_node and is_without_parents:
            are_all_tasks_skipped, is_task_skipped = _check_if_tasks_are_skipped(
                node, dag, is_task_skipped
            )
            if not are_all_tasks_skipped:
                try:
                    dag.nodes[node]["node"].state()
                except NodeNotFoundError:
                    # Shorten node names for better printing.
                    missing_root_nodes.append(node)

    if missing_root_nodes:
        all_names = missing_root_nodes + [
            successor
            for node in missing_root_nodes
            for successor in dag.successors(node)
            if not is_task_skipped[successor]
        ]
        common_ancestor = find_common_ancestor_of_nodes(*all_names)
        dictionary = {}
        for node in missing_root_nodes:
            short_node_name = reduce_node_name(
                dag.nodes[node]["node"], [common_ancestor]
            )
            not_skipped_successors = [
                task for task in dag.successors(node) if not is_task_skipped[task]
            ]
            short_successors = reduce_names_of_multiple_nodes(
                not_skipped_successors, dag, [common_ancestor]
            )
            dictionary[short_node_name] = short_successors

        text = _format_dictionary_to_tree(dictionary, "Missing dependencies:")
        raise ResolvingDependenciesError(_TEMPLATE_ERROR.format(text)) from None


def _check_if_tasks_are_skipped(
    node: MetaNode, dag: nx.DiGraph, is_task_skipped: Dict[str, bool]
) -> Tuple[bool, Dict[str, bool]]:
    """Check for a given node whether it is only used by skipped tasks."""
    are_all_tasks_skipped = []
    for successor in dag.successors(node):
        if successor not in is_task_skipped:
            is_task_skipped[successor] = _check_if_task_is_skipped(successor, dag)
        are_all_tasks_skipped.append(is_task_skipped[successor])

    return all(are_all_tasks_skipped), is_task_skipped


def _check_if_task_is_skipped(task_name: str, dag: nx.DiGraph) -> bool:
    task = dag.nodes[task_name]["task"]
    is_skipped = get_specific_markers_from_task(task, "skip")

    if is_skipped:
        return True

    skip_if_markers = get_specific_markers_from_task(task, "skipif")
    is_any_true = any(
        _skipif(*marker.args, **marker.kwargs)[0] for marker in skip_if_markers
    )
    return is_any_true


def _skipif(condition: bool, *, reason: str) -> Tuple[bool, str]:
    """Shameless copy to circumvent circular imports."""
    return condition, reason


def _format_dictionary_to_tree(dict_: Dict[str, List[str]], title: str) -> str:
    """Format missing root nodes."""
    tree = Tree(title)

    for node, tasks in dict_.items():
        branch = tree.add(Text.assemble(FILE_ICON, node))
        for task in tasks:
            branch.add(Text.assemble(TASK_ICON, task))

    text = render_to_string(tree, console=console, strip_styles=True)
    return text


def _check_if_tasks_have_the_same_products(dag: nx.DiGraph) -> None:
    nodes_created_by_multiple_tasks = []

    for node in dag.nodes:
        is_node = "node" in dag.nodes[node]
        if is_node:
            parents = list(dag.predecessors(node))
            if len(parents) > 1:
                nodes_created_by_multiple_tasks.append(node)

    if nodes_created_by_multiple_tasks:
        all_names = nodes_created_by_multiple_tasks + [
            predecessor
            for node in nodes_created_by_multiple_tasks
            for predecessor in dag.predecessors(node)
        ]
        common_ancestor = find_common_ancestor_of_nodes(*all_names)
        dictionary = {}
        for node in nodes_created_by_multiple_tasks:
            short_node_name = reduce_node_name(
                dag.nodes[node]["node"], [common_ancestor]
            )
            short_predecessors = reduce_names_of_multiple_nodes(
                dag.predecessors(node), dag, [common_ancestor]
            )
            dictionary[short_node_name] = short_predecessors
        text = _format_dictionary_to_tree(dictionary, "Products from multiple tasks:")
        raise ResolvingDependenciesError(
            "There are some tasks which produce the same output. See the following "
            "tree which shows which products are produced by multiple tasks."
            f"\n\n{text}"
        )


@hookimpl
def pytask_resolve_dependencies_log(
    session: Session, report: ResolvingDependenciesReport
) -> None:
    """Log errors which happened while resolving dependencies."""
    console.print()
    console.rule(
        Text("Failures during resolving dependencies", style="failed"),
        style="failed",
    )

    console.print()
    console.print(render_exc_info(*report.exc_info, session.config["show_locals"]))

    console.print()
    console.rule(style="failed")
