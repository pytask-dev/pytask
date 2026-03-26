"""Contains scheduler protocols and implementations."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Protocol

from _pytask.dag_graph import DiGraph
from _pytask.dag_graph import NoCycleError
from _pytask.dag_graph import ancestors
from _pytask.dag_graph import find_cycle
from _pytask.mark_utils import has_mark

if TYPE_CHECKING:
    from _pytask.node_protocols import PTask


class PScheduler(Protocol):
    """Protocol for schedulers that dispatch ready tasks."""

    def get_ready(self, n: int = 1) -> list[str]:
        """Get up to ``n`` tasks which are ready."""

    def is_active(self) -> bool:
        """Indicate whether there are still tasks left."""

    def done(self, *nodes: str) -> None:
        """Mark some tasks as done."""

    def rebuild(self, dag: DiGraph) -> PScheduler:
        """Rebuild the scheduler from an updated DAG while preserving state."""


@dataclass
class SimpleScheduler:
    """The default scheduler based on topological sorting."""

    dag: DiGraph
    priorities: dict[str, int] = field(default_factory=dict)
    _nodes_processing: set[str] = field(default_factory=set)
    _nodes_done: set[str] = field(default_factory=set)

    @classmethod
    def from_dag(cls, dag: DiGraph) -> SimpleScheduler:
        """Instantiate from a DAG."""
        cls.check_dag(dag)

        tasks = [
            dag.nodes[node]["task"] for node in dag.nodes if "task" in dag.nodes[node]
        ]
        priorities = _extract_priorities_from_tasks(tasks)

        task_signatures = {task.signature for task in tasks}
        task_dag = DiGraph()
        for signature in task_signatures:
            task_dag.add_node(signature)
        for signature in task_signatures:
            # The scheduler graph uses edges from predecessor -> successor so that
            # zero in-degree means "ready to run". This is the same orientation the
            # previous networkx-based implementation reached after calling reverse().
            for ancestor_ in ancestors(dag, signature) & task_signatures:
                task_dag.add_edge(ancestor_, signature)

        return cls(dag=task_dag, priorities=priorities)

    @classmethod
    def from_dag_and_sorter(
        cls, dag: DiGraph, sorter: SimpleScheduler
    ) -> SimpleScheduler:
        """Instantiate a sorter from another sorter and a DAG."""
        new_sorter = cls.from_dag(dag)
        new_sorter.done(*sorter._nodes_done)
        new_sorter._nodes_processing = sorter._nodes_processing
        return new_sorter

    @staticmethod
    def check_dag(dag: DiGraph) -> None:
        if not dag.is_directed():
            msg = "Only directed graphs have a topological order."
            raise ValueError(msg)

        try:
            find_cycle(dag)
        except NoCycleError:
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

    def rebuild(self, dag: DiGraph) -> SimpleScheduler:
        """Rebuild the scheduler from an updated DAG while preserving state."""
        return self.from_dag_and_sorter(dag, self)


def _extract_priorities_from_tasks(tasks: list[PTask]) -> dict[str, int]:
    """Extract priorities from tasks.

    Priorities are set via the [pytask.mark.try_first][] and [pytask.mark.try_last][]
    markers. We recode these markers to numeric values to sort all available by
    priorities. ``try_first`` is assigned the highest value such that it has the
    rightmost position in the list. Then, we can simply call `list.pop` on the
    list which is far more efficient than ``list.pop(0)``.

    """
    priorities = {
        task.signature: {
            "try_first": has_mark(task, "try_first"),
            "try_last": has_mark(task, "try_last"),
        }
        for task in tasks
    }

    numeric_mapping = {(True, False): 1, (False, False): 0, (False, True): -1}
    return {
        name: numeric_mapping[(p["try_first"], p["try_last"])]
        for name, p in priorities.items()
    }
