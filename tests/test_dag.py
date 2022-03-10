from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import networkx as nx
import pytest
from _pytask.dag import _extract_priorities_from_tasks
from _pytask.dag import descending_tasks
from _pytask.dag import node_and_neighbors
from _pytask.dag import task_and_descending_tasks
from _pytask.dag import TopologicalSorter
from pytask import Mark
from pytask import Task


@pytest.fixture()
def dag():
    dag = nx.DiGraph()
    for i in range(4):
        dag.add_node(f".::{i}", task=Task(base_name=str(i), path=Path(), function=None))
        dag.add_node(
            f".::{i + 1}", task=Task(base_name=str(i + 1), path=Path(), function=None)
        )
        dag.add_edge(f".::{i}", f".::{i + 1}")

    return dag


@pytest.mark.unit
def test_sort_tasks_topologically(dag):
    topo_ordering = list(TopologicalSorter.from_dag(dag).static_order())
    assert topo_ordering == [f".::{i}" for i in range(5)]


@pytest.mark.unit
def test_descending_tasks(dag):
    for i in range(5):
        descendants = sorted(descending_tasks(f".::{i}", dag))
        assert descendants == [f".::{i}" for i in range(i + 1, 5)]


@pytest.mark.unit
def test_task_and_descending_tasks(dag):
    for i in range(5):
        descendants = sorted(task_and_descending_tasks(f".::{i}", dag))
        assert descendants == [f".::{i}" for i in range(i, 5)]


@pytest.mark.unit
def test_node_and_neighbors(dag):
    for i in range(1, 4):
        nodes = sorted(node_and_neighbors(dag, f".::{i}"))
        assert nodes == [f".::{j}" for j in range(i - 1, i + 2)]


@pytest.mark.unit
@pytest.mark.parametrize(
    "tasks, expectation, expected",
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
            {".::1": -1},
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
            {".::1": 1},
            id="test try_first",
        ),
        pytest.param(
            [Task(base_name="1", path=Path(), function=None, markers=[])],
            does_not_raise(),
            {".::1": 0},
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
            {".::1": 1, ".::2": 0, ".::3": -1},
        ),
    ],
)
def test_extract_priorities_from_tasks(tasks, expectation, expected):
    with expectation:
        result = _extract_priorities_from_tasks(tasks)
        assert result == expected


@pytest.mark.unit
def test_raise_error_for_undirected_graphs(dag):
    undirected_graph = dag.to_undirected()
    with pytest.raises(ValueError, match="Only directed graphs have a"):
        TopologicalSorter.from_dag(undirected_graph)


@pytest.mark.unit
def test_raise_error_for_cycle_in_graph(dag):
    dag.add_edge(".::4", ".::1")
    scheduler = TopologicalSorter.from_dag(dag)
    with pytest.raises(ValueError, match="The DAG contains cycles."):
        scheduler.prepare()


@pytest.mark.unit
def test_raise_if_topological_sorter_is_not_prepared(dag):
    scheduler = TopologicalSorter.from_dag(dag)
    with pytest.raises(ValueError, match="The TopologicalSorter needs to be prepared."):
        scheduler.get_ready(1)


@pytest.mark.unit
def test_ask_for_invalid_number_of_ready_tasks(dag):
    scheduler = TopologicalSorter.from_dag(dag)
    scheduler.prepare()
    with pytest.raises(ValueError, match="'n' must be"):
        scheduler.get_ready(0)


@pytest.mark.unit
def test_reset_topological_sorter(dag):
    scheduler = TopologicalSorter.from_dag(dag)
    scheduler.prepare()
    name = scheduler.get_ready()[0]
    scheduler.done(name)

    assert scheduler._is_prepared
    assert name not in scheduler.dag.nodes

    scheduler.reset()

    assert not scheduler._is_prepared
    assert name in scheduler.dag.nodes
