from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from _pytask.dag_graph import DiGraph
from _pytask.dag_utils import descending_tasks
from _pytask.dag_utils import node_and_neighbors
from _pytask.dag_utils import task_and_descending_tasks
from _pytask.scheduler import SimpleScheduler
from pytask import Mark
from pytask import Task
from tests.conftest import noop


@pytest.fixture
def dag():
    """Create a dag with five nodes in a line."""
    dag = DiGraph()
    for i in range(4):
        task = Task(base_name=str(i), path=Path(), function=noop)
        next_task = Task(base_name=str(i + 1), path=Path(), function=noop)
        dag.add_node(task.signature, task=task)
        dag.add_node(next_task.signature, task=next_task)
        dag.add_edge(task.signature, next_task.signature)

    return dag


def test_sort_tasks_topologically(dag):
    sorter = SimpleScheduler.from_dag(dag)
    topo_ordering = []
    while sorter.is_active():
        task_name = sorter.get_ready()[0]
        topo_ordering.append(task_name)
        sorter.done(task_name)
    topo_names = [dag.nodes[sig]["task"].name for sig in topo_ordering]
    assert topo_names == [f".::{i}" for i in range(5)]


def test_descending_tasks(dag):
    for i in range(5):
        task = next(
            dag.nodes[sig]["task"]
            for sig in dag.nodes
            if dag.nodes[sig]["task"].name == f".::{i}"
        )
        descendants = descending_tasks(task.signature, dag)
        descendant_names = sorted(dag.nodes[sig]["task"].name for sig in descendants)
        assert descendant_names == [f".::{i}" for i in range(i + 1, 5)]


def test_task_and_descending_tasks(dag):
    for i in range(5):
        task = next(
            dag.nodes[sig]["task"]
            for sig in dag.nodes
            if dag.nodes[sig]["task"].name == f".::{i}"
        )
        descendants = task_and_descending_tasks(task.signature, dag)
        descendant_names = sorted(dag.nodes[sig]["task"].name for sig in descendants)
        assert descendant_names == [f".::{i}" for i in range(i, 5)]


def test_node_and_neighbors(dag):
    for i in range(1, 4):
        task = next(
            dag.nodes[sig]["task"]
            for sig in dag.nodes
            if dag.nodes[sig]["task"].name == f".::{i}"
        )
        nodes = node_and_neighbors(dag, task.signature)
        node_names = [dag.nodes[sig]["task"].name for sig in nodes]
        assert node_names == [f".::{j}" for j in range(i - 1, i + 2)]


def test_prioritize_try_first_and_try_last_tasks():
    dag = DiGraph()
    first = Task(
        base_name="first",
        path=Path(),
        function=noop,
        markers=[Mark("try_first", (), {})],
    )
    default = Task(base_name="default", path=Path(), function=noop)
    last = Task(
        base_name="last",
        path=Path(),
        function=noop,
        markers=[Mark("try_last", (), {})],
    )

    for task in (first, default, last):
        dag.add_node(task.signature, task=task)

    scheduler = SimpleScheduler.from_dag(dag)

    first_batch = scheduler.get_ready(3)
    first_batch_names = [dag.nodes[sig]["task"].name for sig in first_batch]

    assert first_batch_names[-1] == ".::first"
    assert first_batch_names[0] == ".::last"


@dataclass
class _UndirectedGraphStub:
    def is_directed(self):
        return False


def test_raise_error_for_undirected_graphs():
    with pytest.raises(ValueError, match="Only directed graphs have a"):
        SimpleScheduler.from_dag(_UndirectedGraphStub())  # type: ignore[arg-type]


def test_raise_error_for_cycle_in_graph(dag):
    dag.add_edge(
        "115f685b0af2aef0c7317a0b48562f34cfb7a622549562bd3d34d4d948b4fdab",
        "55c6cef62d3e62d5f8fc65bb846e66d8d0d3ca60608c04f6f7b095ea073a7dcf",
    )
    with pytest.raises(ValueError, match=r"The DAG contains cycles\."):
        SimpleScheduler.from_dag(dag)


def test_ask_for_invalid_number_of_ready_tasks(dag):
    scheduler = SimpleScheduler.from_dag(dag)
    with pytest.raises(ValueError, match="'n' must be"):
        scheduler.get_ready(0)


def test_instantiate_sorter_from_other_sorter(dag):
    name_to_sig = {dag.nodes[sig]["task"].name: sig for sig in dag.nodes}

    scheduler = SimpleScheduler.from_dag(dag)
    for _ in range(2):
        task_name = scheduler.get_ready()[0]
        scheduler.done(task_name)
    assert scheduler._nodes_done == {name_to_sig[name] for name in (".::0", ".::1")}

    task = Task(base_name="5", path=Path(), function=noop)
    dag.add_node(task.signature, task=Task(base_name="5", path=Path(), function=noop))
    dag.add_edge(name_to_sig[".::4"], task.signature)

    new_scheduler = scheduler.rebuild(dag)
    while new_scheduler.is_active():
        task_name = new_scheduler.get_ready()[0]
        new_scheduler.done(task_name)
    assert new_scheduler._nodes_done == set(name_to_sig.values()) | {task.signature}
