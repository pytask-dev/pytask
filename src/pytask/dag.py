import itertools

import networkx as nx


def sort_tasks_topologically(dag):
    for node in nx.topological_sort(dag):
        if "task" in dag.nodes[node]:
            yield node


def task_and_descending_tasks(task_name, dag):
    yield task_name
    for descendant in nx.descendants(dag, task_name):
        if "task" in dag.nodes[descendant]:
            yield descendant


def node_and_neigbors(dag, node):
    return itertools.chain([node], dag.neighbors(node))
