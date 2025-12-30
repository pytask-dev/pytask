"""Contains code related to the DAG."""

from __future__ import annotations

import itertools
import sys
from typing import TYPE_CHECKING

import networkx as nx
from rich.text import Text
from rich.tree import Tree

from _pytask.console import ARROW_DOWN_ICON
from _pytask.console import FILE_ICON
from _pytask.console import TASK_ICON
from _pytask.console import console
from _pytask.console import format_node_name
from _pytask.console import format_task_name
from _pytask.console import render_to_string
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.mark import select_by_after_keyword
from _pytask.mark import select_tasks_by_marks_and_expressions
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import PTask
from _pytask.nodes import PythonNode
from _pytask.reports import DagReport
from _pytask.shared import reduce_names_of_multiple_nodes
from _pytask.tree_util import tree_map

if TYPE_CHECKING:
    from pathlib import Path

    from _pytask.session import Session


__all__ = ["create_dag", "create_dag_from_session"]


def create_dag(session: Session) -> nx.DiGraph:
    """Create a directed acyclic graph (DAG) for the workflow."""
    try:
        dag = create_dag_from_session(session)
    except Exception:  # noqa: BLE001
        report = DagReport.from_exception(sys.exc_info())
        _log_dag(report=report)
        session.dag_report = report

        raise ResolvingDependenciesError from None
    return dag


def create_dag_from_session(session: Session) -> nx.DiGraph:
    """Create a DAG from a session."""
    dag = _create_dag_from_tasks(tasks=session.tasks)
    _check_if_dag_has_cycles(dag)
    _check_if_tasks_have_the_same_products(dag, session.config["paths"])
    dag = _modify_dag(session=session, dag=dag)
    select_tasks_by_marks_and_expressions(session=session, dag=dag)
    return dag


def _create_dag_from_tasks(tasks: list[PTask]) -> nx.DiGraph:
    """Create the DAG from tasks, dependencies and products."""

    def _add_dependency(
        dag: nx.DiGraph, task: PTask, node: PNode | PProvisionalNode
    ) -> None:
        """Add a dependency to the DAG."""
        dag.add_node(node.signature, node=node)
        dag.add_edge(node.signature, task.signature)

        # If a node is a PythonNode wrapped in another PythonNode, it is a product from
        # another task that is a dependency in the current task. Thus, draw an edge
        # connecting the two nodes.
        if isinstance(node, PythonNode) and isinstance(node.value, PythonNode):
            dag.add_edge(node.value.signature, node.signature)

    def _add_product(
        dag: nx.DiGraph, task: PTask, node: PNode | PProvisionalNode
    ) -> None:
        """Add a product to the DAG."""
        dag.add_node(node.signature, node=node)
        dag.add_edge(task.signature, node.signature)

    dag = nx.DiGraph()

    for task in tasks:
        dag.add_node(task.signature, task=task)

        tree_map(lambda x: _add_dependency(dag, task, x), task.depends_on)
        tree_map(lambda x: _add_product(dag, task, x), task.produces)

        # If a node is a PythonNode wrapped in another PythonNode, it is a product from
        # another task that is a dependency in the current task. Thus, draw an edge
        # connecting the two nodes.
        tree_map(
            lambda x: dag.add_edge(x.value.signature, x.signature)
            if isinstance(x, PythonNode) and isinstance(x.value, PythonNode)
            else None,
            task.depends_on,
        )
    return dag


def _modify_dag(session: Session, dag: nx.DiGraph) -> nx.DiGraph:
    """Create dependencies between tasks when using ``@task(after=...)``."""
    temporary_id_to_task = {
        task.attributes["collection_id"]: task
        for task in session.tasks
        if "collection_id" in task.attributes
    }
    for task in session.tasks:
        after = task.attributes.get("after")
        if isinstance(after, list):
            for temporary_id in after:
                other_task = temporary_id_to_task[temporary_id]
                for successor in dag.successors(other_task.signature):
                    dag.add_edge(successor, task.signature)
        elif isinstance(after, str):
            task_signature = task.signature
            signatures = select_by_after_keyword(session, after)
            signatures.discard(task_signature)
            for signature in signatures:
                for successor in dag.successors(signature):
                    dag.add_edge(successor, task.signature)
    return dag


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
            "nodes in the graph which forms the cycle.\n\n"
            f"{_format_cycles(dag, cycles)}"
        )
        raise ResolvingDependenciesError(msg)


def _format_cycles(dag: nx.DiGraph, cycles: list[tuple[str, ...]]) -> str:
    """Format cycles as a paths connected by arrows."""
    chain = [
        x for i, x in enumerate(itertools.chain.from_iterable(cycles)) if i % 2 == 0
    ]
    chain += [cycles[-1][1]]

    lines: list[str] = []
    for x in chain:
        node = dag.nodes[x].get("task") or dag.nodes[x].get("node")
        if isinstance(node, PTask):
            short_name = format_task_name(node, editor_url_scheme="no_link").plain
        elif isinstance(node, (PNode, PProvisionalNode)):
            short_name = node.name
        lines.extend((short_name, "     " + ARROW_DOWN_ICON))
    # Join while removing last arrow.
    return "\n".join(lines[:-1])


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


def _log_dag(report: DagReport) -> None:
    """Log errors which happened while resolving dependencies."""
    console.print()
    console.rule(
        Text("Failures during resolving dependencies", style="failed"), style="failed"
    )
    console.print()
    console.print(report)
    console.print()
    console.rule(style="failed")
