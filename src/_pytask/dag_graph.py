"""Internal DAG implementation used by pytask."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from _pytask.compat import import_optional_dependency

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Iterator
    from collections.abc import Mapping

    from _pytask.node_protocols import PNode
    from _pytask.node_protocols import PProvisionalNode
    from _pytask.node_protocols import PTask


class NoCycleError(Exception):
    """Raised when no cycle is found in a graph."""


@dataclass(slots=True)
class DAGNode:
    """Payload stored for nodes in pytask's internal DAG."""

    task: PTask | None = None
    node: PNode | PProvisionalNode | None = None

    def __post_init__(self) -> None:
        if (self.task is None) == (self.node is None):
            msg = "A DAG node must store exactly one of 'task' or 'node'."
            raise ValueError(msg)

    @classmethod
    def from_task(cls, task: PTask) -> DAGNode:
        """Create a DAG node from a task."""
        return cls(task=task)

    @classmethod
    def from_node(cls, node: PNode | PProvisionalNode) -> DAGNode:
        """Create a DAG node from a dependency or product node."""
        return cls(node=node)

    @property
    def value(self) -> PTask | PNode | PProvisionalNode:
        """Return the wrapped task or node."""
        if self.task is not None:
            return self.task
        return cast("PNode | PProvisionalNode", self.node)

    def task_or_raise(self) -> PTask:
        """Return the wrapped task."""
        if self.task is None:
            msg = "Expected DAG payload to contain a task."
            raise TypeError(msg)
        return self.task

    def node_or_raise(self) -> PNode | PProvisionalNode:
        """Return the wrapped dependency or product node."""
        if self.node is None:
            msg = "Expected DAG payload to contain a node."
            raise TypeError(msg)
        return self.node


@dataclass
class DAG:
    """A minimal directed graph tailored to pytask's needs."""

    _node_data: dict[str, DAGNode] = field(default_factory=dict)
    _successors: dict[str, set[str]] = field(default_factory=dict)
    _predecessors: dict[str, set[str]] = field(default_factory=dict)

    @property
    def nodes(self) -> dict[str, DAGNode]:
        return self._node_data

    def add_node(self, node_name: str, data: DAGNode) -> None:
        if node_name not in self._node_data:
            self._successors[node_name] = set()
            self._predecessors[node_name] = set()
        self._node_data[node_name] = data

    def add_edge(self, source: str, target: str) -> None:
        if source not in self._node_data or target not in self._node_data:
            msg = "Both nodes must exist before adding an edge."
            raise KeyError(msg)
        self._successors[source].add(target)
        self._predecessors[target].add(source)

    def successors(self, node: str) -> Iterator[str]:
        return iter(self._successors[node])

    def predecessors(self, node: str) -> Iterator[str]:
        return iter(self._predecessors[node])

    def in_degree(self) -> Iterator[tuple[str, int]]:
        for node, predecessors_ in self._predecessors.items():
            yield node, len(predecessors_)

    def remove_nodes_from(self, nodes: Iterable[str]) -> None:
        for node in nodes:
            if node not in self._node_data:
                continue
            for predecessor in tuple(self._predecessors[node]):
                self._successors[predecessor].discard(node)
            for successor in tuple(self._successors[node]):
                self._predecessors[successor].discard(node)
            del self._node_data[node]
            del self._successors[node]
            del self._predecessors[node]

    def is_directed(self) -> bool:
        return True

    def reverse(self) -> DAG:
        graph = DAG()
        for node, data in self._node_data.items():
            graph.add_node(node, data)
        for source, successors in self._successors.items():
            for target in successors:
                graph.add_edge(target, source)
        return graph

    def relabel_nodes(self, mapping: Mapping[str, str]) -> DAG:
        graph = DAG()

        new_labels = [mapping.get(node, node) for node in self._node_data]
        if len(new_labels) != len(set(new_labels)):
            msg = "Relabeling nodes requires unique target labels."
            raise ValueError(msg)

        for node, data in self._node_data.items():
            graph.add_node(mapping.get(node, node), data)
        for source, successors in self._successors.items():
            new_source = mapping.get(source, source)
            for target in successors:
                graph.add_edge(new_source, mapping.get(target, target))
        return graph

    def to_networkx(self) -> Any:
        nx = cast("Any", import_optional_dependency("networkx"))
        graph = nx.DiGraph()
        for node in self._node_data:
            graph.add_node(node)
        for source, successors in self._successors.items():
            for target in successors:
                graph.add_edge(source, target)
        return graph


def descendants(dag: DAG, node: str) -> set[str]:
    """Return all descendants of a node."""
    return _traverse(dag, node, dag.successors)


def ancestors(dag: DAG, node: str) -> set[str]:
    """Return all ancestors of a node."""
    return _traverse(dag, node, dag.predecessors)


def _traverse(
    _dag: DAG,
    node: str,
    adjacency: Callable[[str], Iterable[str]],
) -> set[str]:
    visited: set[str] = set()
    stack = list(adjacency(node))

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        stack.extend(adjacency(current))

    return visited


def find_cycle(
    dag: DAG,
) -> list[tuple[str, str]]:
    """Find one cycle in the graph."""
    visited: set[str] = set()
    active: set[str] = set()
    path: list[str] = []

    def _visit(node: str) -> list[tuple[str, str]] | None:
        visited.add(node)
        active.add(node)
        path.append(node)

        for successor in dag.successors(node):
            if successor not in visited:
                cycle = _visit(successor)
                if cycle is not None:
                    return cycle
            elif successor in active:
                start = path.index(successor)
                cycle_nodes = [*path[start:], successor]
                return list(itertools.pairwise(cycle_nodes))

        active.remove(node)
        path.pop()
        return None

    for node in dag.nodes:
        if node in visited:
            continue
        cycle = _visit(node)
        if cycle is not None:
            return cycle

    raise NoCycleError
