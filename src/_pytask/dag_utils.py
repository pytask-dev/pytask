"""Implement some capabilities to deal with the DAG."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from _pytask.node_protocols import PTask

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterable

    from _pytask.dag_graph import DAG


__all__ = [
    "descending_tasks",
    "node_and_neighbors",
    "preceding_tasks",
    "task_and_descending_tasks",
    "task_and_preceding_tasks",
]


def descending_tasks(task_name: str, dag: DAG) -> Generator[str, None, None]:
    """Yield only descending tasks."""
    for descendant in dag.descendants(task_name):
        if isinstance(dag.nodes[descendant], PTask):
            yield descendant


def task_and_descending_tasks(task_name: str, dag: DAG) -> Generator[str, None, None]:
    """Yield task and descending tasks."""
    yield task_name
    yield from descending_tasks(task_name, dag)


def preceding_tasks(task_name: str, dag: DAG) -> Generator[str, None, None]:
    """Yield only preceding tasks."""
    for ancestor in dag.ancestors(task_name):
        if isinstance(dag.nodes[ancestor], PTask):
            yield ancestor


def task_and_preceding_tasks(task_name: str, dag: DAG) -> Generator[str, None, None]:
    """Yield task and preceding tasks."""
    yield task_name
    yield from preceding_tasks(task_name, dag)


def node_and_neighbors(dag: DAG, node: str) -> Iterable[str]:
    """Yield node and neighbors which are first degree predecessors and successors.

    We cannot use ``dag.neighbors`` as it only considers successors as neighbors in a
    DAG.

    The task node needs to be yield in the middle so that first predecessors are checked
    and then the rest of the nodes.

    """
    return itertools.chain(dag.predecessors(node), [node], dag.successors(node))
