from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import networkx as nx
import pytest
from _pytask.dag_utils import _extract_priorities_from_tasks
from _pytask.dag_utils import descending_tasks
from _pytask.dag_utils import node_and_neighbors
from _pytask.dag_utils import task_and_descending_tasks
from _pytask.dag_utils import TopologicalSorter
from pytask import Mark
from pytask import Task


@pytest.fixture()
def dag():
    """Create a dag with five nodes in a line."""
    dag = nx.DiGraph()
    for i in range(4):
        task = Task(base_name=str(i), path=Path(), function=None)
        next_task = Task(base_name=str(i + 1), path=Path(), function=None)
        dag.add_node(task.signature, task=task)
        dag.add_node(next_task.signature, task=next_task)
        dag.add_edge(task.signature, next_task.signature)

    return dag


@pytest.mark.unit()
def test_sort_tasks_topologically(dag):
    sorter = TopologicalSorter.from_dag(dag)
    topo_ordering = []
    while sorter.is_active():
        task_signature = sorter.get_ready()[0]
        topo_ordering.append(task_signature)
        sorter.done(task_signature)
    topo_names = [dag.nodes[sig]["task"].name for sig in topo_ordering]
    assert topo_names == [f".::{i}" for i in range(5)]


@pytest.mark.unit()
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


@pytest.mark.unit()
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


@pytest.mark.unit()
def test_node_and_neighbors(dag):
    for i in range(1, 4):
        task = next(
            dag.nodes[sig]["task"]
            for sig in dag.nodes
            if dag.nodes[sig]["task"].name == f".::{i}"
        )
        nodes = node_and_neighbors(dag, task.signature)
        node_names = sorted(dag.nodes[sig]["task"].name for sig in nodes)
        assert node_names == [f".::{j}" for j in range(i - 1, i + 2)]


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("tasks", "expectation", "expected"),
    [
        pytest.param(
            [
                Task(
                    base_name="1",
                    path=Path(),
                    function=None,
                    markers=[Mark("try_last", (), {})],
                )
            ],
            does_not_raise(),
            {"c12d8d4f7e2e3128d27878d1fb3d8e3583e90e68000a13634dfbf21f4d1456f3": -1},
            id="test try_last",
        ),
        pytest.param(
            [
                Task(
                    base_name="1",
                    path=Path(),
                    function=None,
                    markers=[Mark("try_first", (), {})],
                )
            ],
            does_not_raise(),
            {"c12d8d4f7e2e3128d27878d1fb3d8e3583e90e68000a13634dfbf21f4d1456f3": 1},
            id="test try_first",
        ),
        pytest.param(
            [Task(base_name="1", path=Path(), function=None, markers=[])],
            does_not_raise(),
            {"c12d8d4f7e2e3128d27878d1fb3d8e3583e90e68000a13634dfbf21f4d1456f3": 0},
            id="test no priority",
        ),
        pytest.param(
            [
                Task(
                    base_name="1",
                    path=Path(),
                    function=None,
                    markers=[Mark("try_first", (), {}), Mark("try_last", (), {})],
                )
            ],
            pytest.raises(ValueError, match="'try_first' and 'try_last' cannot be"),
            {".::1": 1},
            id="test mixed priorities",
        ),
        pytest.param(
            [
                Task(
                    base_name="1",
                    path=Path(),
                    function=None,
                    markers=[Mark("try_first", (), {})],
                ),
                Task(base_name="2", path=Path(), function=None, markers=[]),
                Task(
                    base_name="3",
                    path=Path(),
                    function=None,
                    markers=[Mark("try_last", (), {})],
                ),
            ],
            does_not_raise(),
            {
                "c12d8d4f7e2e3128d27878d1fb3d8e3583e90e68000a13634dfbf21f4d1456f3": 1,
                "c5f667e69824043475b1283ed8920e513cb4343ec7077f71a3d9f5972f5204b9": 0,
                "dca295f815f54d282b33e8d9398cea4962d0dfbe881d2ab28fc48ff9e060203a": -1,
            },
        ),
    ],
)
def test_extract_priorities_from_tasks(tasks, expectation, expected):
    with expectation:
        result = _extract_priorities_from_tasks(tasks)
        assert result == expected


@pytest.mark.unit()
def test_raise_error_for_undirected_graphs(dag):
    undirected_graph = dag.to_undirected()
    with pytest.raises(ValueError, match="Only directed graphs have a"):
        TopologicalSorter.from_dag(undirected_graph)


@pytest.mark.unit()
def test_raise_error_for_cycle_in_graph(dag):
    dag.add_edge(
        "115f685b0af2aef0c7317a0b48562f34cfb7a622549562bd3d34d4d948b4fdab",
        "55c6cef62d3e62d5f8fc65bb846e66d8d0d3ca60608c04f6f7b095ea073a7dcf",
    )
    with pytest.raises(ValueError, match="The DAG contains cycles."):
        TopologicalSorter.from_dag(dag)


@pytest.mark.unit()
def test_ask_for_invalid_number_of_ready_tasks(dag):
    scheduler = TopologicalSorter.from_dag(dag)
    with pytest.raises(ValueError, match="'n' must be"):
        scheduler.get_ready(0)


@pytest.mark.unit()
def test_instantiate_sorter_from_other_sorter(dag):
    name_to_signature = {
        dag.nodes[signature]["task"].name: signature for signature in dag.nodes
    }

    scheduler = TopologicalSorter.from_dag(dag)
    for _ in range(2):
        task_signature = scheduler.get_ready()[0]
        scheduler.done(task_signature)
    assert scheduler._nodes_done == {
        name_to_signature[name] for name in (".::0", ".::1")
    }

    dag.add_node(".::5", task=Task(base_name="5", path=Path(), function=None))
    dag.add_edge(".::4", ".::5")

    new_scheduler = TopologicalSorter.from_dag_and_sorter(dag, scheduler)
    while new_scheduler.is_active():
        task_signature = new_scheduler.get_ready()[0]
        new_scheduler.done(task_signature)
    assert new_scheduler._nodes_done == set(name_to_signature.values())
