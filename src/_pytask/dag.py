"""Implement some capabilities to deal with the DAG."""
from __future__ import annotations

import itertools
from typing import Dict
from typing import Generator
from typing import Iterable
from typing import Set

import attr
import networkx as nx
from _pytask.console import format_strings_as_flat_tree
from _pytask.console import TASK_ICON
from _pytask.mark_utils import has_mark
from _pytask.nodes import Task


def descending_tasks(task_name: str, dag: nx.DiGraph) -> Generator[str, None, None]:
    """Yield only descending tasks."""
    for descendant in nx.descendants(dag, task_name):
        if "task" in dag.nodes[descendant]:
            yield descendant


def task_and_descending_tasks(
    task_name: str, dag: nx.DiGraph
) -> Generator[str, None, None]:
    """Yield task and descending tasks."""
    yield task_name
    yield from descending_tasks(task_name, dag)


def preceding_tasks(task_name: str, dag: nx.DiGraph) -> Generator[str, None, None]:
    """Yield only preceding tasks."""
    for ancestor in nx.ancestors(dag, task_name):
        if "task" in dag.nodes[ancestor]:
            yield ancestor


def task_and_preceding_tasks(
    task_name: str, dag: nx.DiGraph
) -> Generator[str, None, None]:
    """Yield task and preceding tasks."""
    yield task_name
    yield from preceding_tasks(task_name, dag)


def node_and_neighbors(dag: nx.DiGraph, node: str) -> Iterable[str]:
    """Yield node and neighbors which are first degree predecessors and successors.

    We cannot use ``dag.neighbors`` as it only considers successors as neighbors in a
    DAG.

    """
    return itertools.chain([node], dag.predecessors(node), dag.successors(node))


@attr.s
class TopologicalSorter:
    """The topological sorter class.

    This class allows to perform a topological sort

    """

    dag = attr.ib(type=nx.DiGraph)
    priorities = attr.ib(factory=dict, type=Dict[str, int])
    _dag_backup = attr.ib(default=None, type=nx.DiGraph)
    _is_prepared = attr.ib(default=False, type=bool)
    _nodes_out = attr.ib(factory=set, type=Set[str])

    @classmethod
    def from_dag(cls, dag: nx.DiGraph) -> TopologicalSorter:
        """Instantiate from a DAG."""
        if not dag.is_directed():
            raise ValueError("Only directed graphs have a topological order.")

        tasks = [
            dag.nodes[node]["task"] for node in dag.nodes if "task" in dag.nodes[node]
        ]
        priorities = _extract_priorities_from_tasks(tasks)

        task_names = {task.name for task in tasks}
        task_dict = {name: nx.ancestors(dag, name) & task_names for name in task_names}
        task_dag = nx.DiGraph(task_dict).reverse()

        return cls(task_dag, priorities, task_dag.copy())

    def prepare(self) -> None:
        """Perform some checks before creating a topological ordering."""
        try:
            nx.algorithms.cycles.find_cycle(self.dag)
        except nx.NetworkXNoCycle:
            pass
        else:
            raise ValueError("The DAG contains cycles.")

        self._is_prepared = True

    def get_ready(self, n: int = 1) -> list[str]:
        """Get up to ``n`` tasks which are ready."""
        if not self._is_prepared:
            raise ValueError("The TopologicalSorter needs to be prepared.")
        if not isinstance(n, int) or n < 1:
            raise ValueError("'n' must be an integer greater or equal than 1.")

        ready_nodes = {v for v, d in self.dag.in_degree() if d == 0} - self._nodes_out
        prioritized_nodes = sorted(
            ready_nodes, key=lambda x: self.priorities.get(x, 0)
        )[-n:]

        self._nodes_out.update(prioritized_nodes)

        return prioritized_nodes

    def is_active(self) -> bool:
        """Indicate whether there are still tasks left."""
        return bool(self.dag.nodes)

    def done(self, *nodes: str) -> None:
        """Mark some tasks as done."""
        self._nodes_out = self._nodes_out - set(nodes)
        self.dag.remove_nodes_from(nodes)

    def reset(self) -> None:
        """Reset an exhausted topological sorter."""
        self.dag = self._dag_backup.copy()
        self._is_prepared = False
        self._nodes_out = set()

    def static_order(self) -> Generator[str, None, None]:
        """Return a topological order of tasks as an iterable."""
        self.prepare()
        while self.is_active():
            new_task = self.get_ready()[0]
            yield new_task
            self.done(new_task)


def _extract_priorities_from_tasks(tasks: list[Task]) -> dict[str, int]:
    """Extract priorities from tasks.

    Priorities are set via the ``pytask.mark.try_first`` and ``pytask.mark.try_last``
    markers. We recode these markers to numeric values to sort all available by
    priorities. ``try_first`` is assigned the highest value such that it has the
    rightmost position in the list. Then, we can simply call :meth:`list.pop` on the
    list which is far more efficient than ``list.pop(0)``.

    """
    priorities = {
        task.name: {
            "try_first": has_mark(task, "try_first"),
            "try_last": has_mark(task, "try_last"),
        }
        for task in tasks
    }
    tasks_w_mixed_priorities = [
        name for name, p in priorities.items() if p["try_first"] and p["try_last"]
    ]

    if tasks_w_mixed_priorities:
        name_to_task = {task.name: task for task in tasks}
        reduced_names = [
            name_to_task[name].short_name for name in tasks_w_mixed_priorities
        ]
        text = format_strings_as_flat_tree(
            reduced_names, "Tasks with mixed priorities", TASK_ICON
        )
        raise ValueError(
            "'try_first' and 'try_last' cannot be applied on the same task. See the "
            f"following tasks for errors:\n\n{text}"
        )

    # Recode to numeric values for sorting.
    numeric_mapping = {(True, False): 1, (False, False): 0, (False, True): -1}
    numeric_priorities = {
        name: numeric_mapping[(p["try_first"], p["try_last"])]
        for name, p in priorities.items()
    }

    return numeric_priorities
