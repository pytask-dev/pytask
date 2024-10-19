"""Implement some capabilities to deal with the DAG."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import networkx as nx
from attrs import define
from attrs import field

from _pytask.mark_utils import has_mark

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterable

    from _pytask.node_protocols import PTask


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

    The task node needs to be yield in the middle so that first predecessors are checked
    and then the rest of the nodes.

    """
    return itertools.chain(dag.predecessors(node), [node], dag.successors(node))


@define
class TopologicalSorter:
    """The topological sorter class.

    This class allows to perform a topological sort#

    Attributes
    ----------
    dag
        Not the full DAG, but a reduced version that only considers tasks.
    priorities
        A dictionary of task names to a priority value. 1 for try first, 0 for the
        default priority and, -1 for try last.

    """

    dag: nx.DiGraph
    priorities: dict[str, int] = field(factory=dict)
    _nodes_processing: set[str] = field(factory=set)
    _nodes_done: set[str] = field(factory=set)

    @classmethod
    def from_dag(cls, dag: nx.DiGraph) -> TopologicalSorter:
        """Instantiate from a DAG."""
        cls.check_dag(dag)

        tasks = [
            dag.nodes[node]["task"] for node in dag.nodes if "task" in dag.nodes[node]
        ]
        priorities = _extract_priorities_from_tasks(tasks)

        task_signatures = {task.signature for task in tasks}
        task_dict = {s: nx.ancestors(dag, s) & task_signatures for s in task_signatures}
        task_dag = nx.DiGraph(task_dict).reverse()

        return cls(dag=task_dag, priorities=priorities)

    @classmethod
    def from_dag_and_sorter(
        cls, dag: nx.DiGraph, sorter: TopologicalSorter
    ) -> TopologicalSorter:
        """Instantiate a sorter from another sorter and a DAG."""
        new_sorter = cls.from_dag(dag)
        new_sorter.done(*sorter._nodes_done)
        new_sorter._nodes_processing = sorter._nodes_processing
        return new_sorter

    @staticmethod
    def check_dag(dag: nx.DiGraph) -> None:
        if not dag.is_directed():
            msg = "Only directed graphs have a topological order."
            raise ValueError(msg)

        try:
            nx.algorithms.cycles.find_cycle(dag)
        except nx.NetworkXNoCycle:
            pass
        else:
            msg = "The DAG contains cycles."
            raise ValueError(msg)

    def get_ready(self, n: int = 1) -> list[str]:
        """Get up to ``n`` tasks which are ready."""
        if not isinstance(n, int) or n < 1:
            msg = "'n' must be an integer greater or equal than 1."
            raise ValueError(msg)

        ready_nodes = {
            v for v, d in self.dag.in_degree() if d == 0
        } - self._nodes_processing
        prioritized_nodes = sorted(
            ready_nodes, key=lambda x: self.priorities.get(x, 0)
        )[-n:]

        self._nodes_processing.update(prioritized_nodes)

        return prioritized_nodes

    def is_active(self) -> bool:
        """Indicate whether there are still tasks left."""
        return bool(self.dag.nodes)

    def done(self, *nodes: str) -> None:
        """Mark some tasks as done."""
        self._nodes_processing = self._nodes_processing - set(nodes)
        self.dag.remove_nodes_from(nodes)
        self._nodes_done.update(nodes)


def _extract_priorities_from_tasks(tasks: list[PTask]) -> dict[str, int]:
    """Extract priorities from tasks.

    Priorities are set via the ``pytask.mark.try_first`` and ``pytask.mark.try_last``
    markers. We recode these markers to numeric values to sort all available by
    priorities. ``try_first`` is assigned the highest value such that it has the
    rightmost position in the list. Then, we can simply call :meth:`list.pop` on the
    list which is far more efficient than ``list.pop(0)``.

    """
    priorities = {
        task.signature: {
            "try_first": has_mark(task, "try_first"),
            "try_last": has_mark(task, "try_last"),
        }
        for task in tasks
    }

    # Recode to numeric values for sorting.
    numeric_mapping = {(True, False): 1, (False, False): 0, (False, True): -1}
    return {
        name: numeric_mapping[(p["try_first"], p["try_last"])]
        for name, p in priorities.items()
    }
