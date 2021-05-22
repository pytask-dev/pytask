import itertools
import sys
from typing import Dict
from typing import List
from typing import Tuple

import networkx as nx
from _pytask.config import hookimpl
from _pytask.config import IS_FILE_SYSTEM_CASE_SENSITIVE
from _pytask.console import ARROW_DOWN_ICON
from _pytask.console import console
from _pytask.console import FILE_ICON
from _pytask.console import TASK_ICON
from _pytask.dag import node_and_neighbors
from _pytask.dag import task_and_descending_tasks
from _pytask.dag import TopologicalSorter
from _pytask.database import State
from _pytask.enums import ColorCode
from _pytask.exceptions import NodeNotFoundError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.mark import Mark
from _pytask.nodes import reduce_names_of_multiple_nodes
from _pytask.nodes import reduce_node_name
from _pytask.path import find_common_ancestor_of_nodes
from _pytask.report import ResolvingDependenciesReport
from pony import orm
from rich.traceback import Traceback
from rich.tree import Tree


@hookimpl
def pytask_resolve_dependencies(session):
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

        raise ResolvingDependenciesError

    else:
        return True


@hookimpl
def pytask_resolve_dependencies_create_dag(tasks):
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

    return dag


@hookimpl
def pytask_resolve_dependencies_select_execution_dag(dag):
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
def pytask_resolve_dependencies_validate_dag(dag):
    """Validate the DAG."""
    _check_if_dag_has_cycles(dag)
    _check_if_root_nodes_are_available(dag)
    _check_if_tasks_have_the_same_products(dag)


def _have_task_or_neighbors_changed(task_name, dag):
    """Indicate whether dependencies or products of a task have changed."""
    return any(
        _has_node_changed(task_name, dag.nodes[node])
        for node in node_and_neighbors(dag, task_name)
    )


@orm.db_session
def _has_node_changed(task_name: str, node_dict):
    """Indicate whether a single dependency or product has changed."""
    node = node_dict.get("task") or node_dict["node"]
    try:
        state = node.state()
    except NodeNotFoundError:
        out = True
    else:
        try:
            state_in_db = State[task_name, node.name].state
        except orm.ObjectNotFound:
            out = True
        else:
            out = state != state_in_db

    return out


def _check_if_dag_has_cycles(dag):
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


def _format_cycles(cycles: List[Tuple[str]]) -> str:
    """Format cycles as a paths connected by arrows."""
    chain = [x for i, x in enumerate(itertools.chain(*cycles)) if i % 2 == 0]
    chain += [cycles[-1][1]]

    lines = chain[:1]
    for x in chain[1:]:
        lines.append("     " + ARROW_DOWN_ICON)
        lines.append(x)
    text = "\n".join(lines)

    return text


_TEMPLATE_ERROR = (
    "Some dependencies do not exist or are not produced by any task. See the following "
    "tree which shows which dependencies are missing for which tasks.\n\n{}"
)
if IS_FILE_SYSTEM_CASE_SENSITIVE:
    _TEMPLATE_ERROR += "\n\n(Hint: Sometimes case sensitivity is at fault.)"


def _check_if_root_nodes_are_available(dag):
    missing_root_nodes = []

    for node in dag.nodes:
        is_node = "node" in dag.nodes[node]
        is_without_parents = len(list(dag.predecessors(node))) == 0
        if is_node and is_without_parents:
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
        ]
        common_ancestor = find_common_ancestor_of_nodes(*all_names)
        dictionary = {}
        for node in missing_root_nodes:
            short_node_name = reduce_node_name(
                dag.nodes[node]["node"], [common_ancestor]
            )
            short_successors = reduce_names_of_multiple_nodes(
                dag.successors(node), dag, [common_ancestor]
            )
            dictionary[short_node_name] = short_successors

        text = _format_dictionary_to_tree(dictionary, "Missing dependencies:")
        raise ResolvingDependenciesError(_TEMPLATE_ERROR.format(text))


def _format_dictionary_to_tree(dict_: Dict[str, List[str]], title: str) -> str:
    """Format missing root nodes."""
    tree = Tree(title)

    for node, tasks in dict_.items():
        branch = tree.add(FILE_ICON + node)
        for task in tasks:
            branch.add(TASK_ICON + task)

    text = "".join(
        [x.text for x in tree.__rich_console__(console, console.options)][:-1]
    )

    return text


def _check_if_tasks_have_the_same_products(dag):
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
def pytask_resolve_dependencies_log(report):
    """Log errors which happened while resolving dependencies."""
    console.print()
    console.rule(
        f"[{ColorCode.FAILED}]Failures during resolving dependencies",
        style=ColorCode.FAILED,
    )

    console.print()
    console.print(Traceback.from_exception(*report.exc_info))

    console.print()
    console.rule(style=ColorCode.FAILED)
