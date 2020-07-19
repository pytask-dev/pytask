import itertools

import networkx as nx


def sort_tasks_topologically(dag):
    for node in nx.topological_sort(dag):
        if "task" in dag.nodes[node]:
            yield node


def descending_tasks(task_name, dag):
    for descendant in nx.descendants(dag, task_name):
        if "task" in dag.nodes[descendant]:
            yield descendant


def task_and_descending_tasks(task_name, dag):
    yield task_name
    yield from descending_tasks(task_name, dag)


def node_and_neigbors(dag, node):
    return itertools.chain([node], dag.neighbors(node))
