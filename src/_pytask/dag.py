"""Implement some capabilities to deal with the DAG."""
import itertools
from typing import List

import attr
import networkx as nx
from _pytask.nodes import MetaTask


def sort_tasks_topologically(dag: nx.DiGraph, tasks: List[MetaTask]):
    """Sort tasks in topological order."""
    scheduler = TopologicalSorter.from_dag_and_tasks(dag, tasks)
    return scheduler.static_order()


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


@attr.s
class TopologicalSorter:

    dag = attr.ib(converter=nx.DiGraph)

    @classmethod
    def from_dag_and_tasks(cls, dag, tasks):
        task_names = {task.name for task in tasks}
        task_dict = {name: nx.ancestors(dag, name) & task_names for name in task_names}
        task_dag = nx.DiGraph(task_dict).reverse()

        return cls(task_dag)

    def prepare(self):
        if not self.dag.is_directed():
            raise ValueError("Only directed graphs have a topological order.")

    def get_ready(self):
        zero_indegree = [v for v, d in self.dag.in_degree() if d == 0]
        return zero_indegree

    def is_active(self):
        return bool(self.dag.nodes)

    def done(self, *nodes):
        self.dag.remove_nodes_from(nodes)

    def static_order(self):
        self.prepare()
        while self.is_active():
            nodes = self.get_ready()
            yield from nodes
            self.done(*nodes)
