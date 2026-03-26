"""Internal DAG implementation used by pytask."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from _pytask.compat import import_optional_dependency

if TYPE_CHECKING:
    from collections.abc import Iterator


class NoCycleError(Exception):
    """Raised when no cycle is found in a graph."""


class NodeView:
    """A minimal mapping-like view over node attributes."""

    def __init__(self, node_attributes: dict[str, dict[str, Any]]) -> None:
        self._node_attributes = node_attributes

    def __getitem__(self, node: str) -> dict[str, Any]:
        return self._node_attributes[node]

    def __iter__(self) -> Iterator[str]:
        return iter(self._node_attributes)

    def __len__(self) -> int:
        return len(self._node_attributes)

    def __contains__(self, node: object) -> bool:
        return node in self._node_attributes


class UndirectedGraph:
    """A minimal undirected graph used for validation tests."""

    def __init__(
        self,
        node_attributes: dict[str, dict[str, Any]],
        adjacency: dict[str, dict[str, None]],
        graph_attributes: dict[str, Any],
    ) -> None:
        self._node_attributes = {
            node: attributes.copy() for node, attributes in node_attributes.items()
        }
        self._adjacency = {
            node: neighbors.copy() for node, neighbors in adjacency.items()
        }
        self.graph = graph_attributes.copy()
        self.nodes = NodeView(self._node_attributes)

    def is_directed(self) -> bool:
        return False


class DiGraph:
    """A minimal directed graph tailored to pytask's needs."""

    def __init__(self) -> None:
        self._node_attributes: dict[str, dict[str, Any]] = {}
        self._successors: dict[str, dict[str, None]] = {}
        self._predecessors: dict[str, dict[str, None]] = {}
        self.graph: dict[str, Any] = {}
        self.nodes = NodeView(self._node_attributes)

    def add_node(self, node_name: str, **attributes: Any) -> None:
        if node_name not in self._node_attributes:
            self._node_attributes[node_name] = {}
            self._successors[node_name] = {}
            self._predecessors[node_name] = {}
        self._node_attributes[node_name].update(attributes)

    def add_edge(self, source: str, target: str) -> None:
        self.add_node(source)
        self.add_node(target)
        self._successors[source][target] = None
        self._predecessors[target][source] = None

    def successors(self, node: str) -> Iterator[str]:
        return iter(self._successors[node])

    def predecessors(self, node: str) -> Iterator[str]:
        return iter(self._predecessors[node])

    def in_degree(self) -> Iterator[tuple[str, int]]:
        for node, predecessors_ in self._predecessors.items():
            yield node, len(predecessors_)

    def remove_nodes_from(self, nodes: list[str] | set[str] | tuple[str, ...]) -> None:
        for node in nodes:
            if node not in self._node_attributes:
                continue
            for predecessor in tuple(self._predecessors[node]):
                self._successors[predecessor].pop(node, None)
            for successor in tuple(self._successors[node]):
                self._predecessors[successor].pop(node, None)
            del self._node_attributes[node]
            del self._successors[node]
            del self._predecessors[node]

    def is_directed(self) -> bool:
        return True

    def reverse(self) -> DiGraph:
        graph = DiGraph()
        graph.graph = self.graph.copy()
        for node, attributes in self._node_attributes.items():
            graph.add_node(node, **attributes.copy())
        for source, successors in self._successors.items():
            for target in successors:
                graph.add_edge(target, source)
        return graph

    def relabel_nodes(self, mapping: dict[str, str]) -> DiGraph:
        graph = DiGraph()
        graph.graph = self.graph.copy()

        new_labels = [mapping.get(node, node) for node in self._node_attributes]
        if len(new_labels) != len(set(new_labels)):
            msg = "Relabeling nodes requires unique target labels."
            raise ValueError(msg)

        for node, attributes in self._node_attributes.items():
            graph.add_node(mapping.get(node, node), **attributes.copy())
        for source, successors in self._successors.items():
            new_source = mapping.get(source, source)
            for target in successors:
                graph.add_edge(new_source, mapping.get(target, target))
        return graph

    def set_node_attributes(self, values: dict[str, Any], name: str) -> None:
        for node, value in values.items():
            if node in self._node_attributes:
                self._node_attributes[node][name] = value

    def to_undirected(self) -> UndirectedGraph:
        adjacency = {
            node: {
                **self._predecessors[node],
                **self._successors[node],
            }
            for node in self._node_attributes
        }
        return UndirectedGraph(self._node_attributes, adjacency, self.graph)

    def to_networkx(self) -> Any:
        nx = cast("Any", import_optional_dependency("networkx"))
        graph = nx.DiGraph()
        graph.graph = self.graph.copy()
        for node, attributes in self._node_attributes.items():
            graph.add_node(node, **attributes.copy())
        for source, successors in self._successors.items():
            for target in successors:
                graph.add_edge(source, target)
        return graph


def descendants(dag: DiGraph, node: str) -> set[str]:
    """Return all descendants of a node."""
    return _traverse(dag, node, dag.successors)


def ancestors(dag: DiGraph, node: str) -> set[str]:
    """Return all ancestors of a node."""
    return _traverse(dag, node, dag.predecessors)


def _traverse(
    _dag: DiGraph,
    node: str,
    adjacency: Any,
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


def find_cycle(dag: DiGraph) -> list[tuple[str, str]]:
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
