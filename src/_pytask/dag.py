"""Implement some capabilities to deal with the DAG."""
import itertools
import pprint
from typing import List

import attr
import networkx as nx
from _pytask.mark import get_specific_markers_from_task
from _pytask.nodes import MetaTask


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


def sort_tasks_topologically(dag: nx.DiGraph, tasks: List[MetaTask]):
    """Sort tasks in topological order."""
    priorities = _extract_priorities_from_tasks(tasks)

    scheduler = _TopologicalSorter.from_dag_and_tasks(dag, tasks)
    scheduler.prepare()
    all_nodes = []
    while scheduler.is_active():
        all_nodes = all_nodes + scheduler.get_ready()
        all_nodes = sorted(set(all_nodes), key=priorities.get)

        new_task = all_nodes.pop()
        yield new_task
        scheduler.done(new_task)


def _extract_priorities_from_tasks(tasks):
    """Extract priorities from tasks.

    Priorities are set via the ``pytask.mark.try_first`` and ``pytask.mark.try_last``
    markers. We recode these markers to numeric values to sort all available by
    priorities. ``try_first`` is assigned the highest value such that it has the
    rightmost position in the list. Then, we can simply call :meth:`list.pop` on the
    list which is far more efficient than ``list.pop(0)``.

    """
    priorities = {
        task.name: {
            "try_first": bool(get_specific_markers_from_task(task, "try_first")),
            "try_last": bool(get_specific_markers_from_task(task, "try_last")),
        }
        for task in tasks
    }
    tasks_w_mixed_priorities = [
        name for name, p in priorities.items() if p["try_first"] and p["try_last"]
    ]
    if tasks_w_mixed_priorities:
        raise ValueError(
            "'try_first' and 'try_last' cannot be applied on the same task. See the "
            f"following tasks for errors:\n\n{pprint.pformat(tasks_w_mixed_priorities)}"
        )

    # Recode to numeric values for sorting.
    numeric_mapping = {(True, False): 1, (False, False): 0, (False, True): -1}
    numeric_priorities = {
        name: numeric_mapping[(p["try_first"], p["try_last"])]
        for name, p in priorities.items()
    }

    return numeric_priorities


@attr.s
class _TopologicalSorter:
    """The topological sorter."""

    dag = attr.ib(converter=nx.DiGraph)
    _is_prepared = attr.ib(default=False, type=bool)

    @classmethod
    def from_dag_and_tasks(cls, dag, tasks):
        task_names = {task.name for task in tasks}
        task_dict = {name: nx.ancestors(dag, name) & task_names for name in task_names}
        task_dag = nx.DiGraph(task_dict).reverse()

        return cls(task_dag)

    def prepare(self):
        if not self.dag.is_directed():
            raise ValueError("Only directed graphs have a topological order.")

        try:
            nx.algorithms.cycles.find_cycle(self.dag)
        except nx.NetworkXNoCycle:
            pass
        else:
            raise ValueError("The DAG contains cycles.")
        self._is_prepared = True

    def get_ready(self):
        if not self._is_prepared:
            raise ValueError("The TopologicalSorter needs to be prepared.")
        return [v for v, d in self.dag.in_degree() if d == 0]

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
