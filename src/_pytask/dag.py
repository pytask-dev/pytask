"""Implement some capabilities to deal with the DAG."""
import itertools

import networkx as nx


def sort_tasks_topologically(dag):
    """Sort tasks in topological ordering."""
    for node in nx.topological_sort(dag):
        if "task" in dag.nodes[node]:
            yield node


def descending_tasks(task_name, dag):
    """Yield only descending tasks."""
    for descendant in nx.descendants(dag, task_name):
        if "task" in dag.nodes[descendant]:
            yield descendant


def task_and_descending_tasks(task_name, dag):
    """Yield task and descending tasks."""
    yield task_name
    yield from descending_tasks(task_name, dag)


def node_and_neighbors(dag, node):
    """Yield node and neighbors which are first degree predecessors and successors.

    We cannot use ``dag.neighbors`` as it only considers successors as neighbors in a
    DAG.

    """
    return itertools.chain([node], dag.predecessors(node), dag.successors(node))
