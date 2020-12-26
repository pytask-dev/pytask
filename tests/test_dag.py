from contextlib import ExitStack as does_not_raise  # noqa: N813

import attr
import networkx as nx
import pytest
from _pytask.dag import _extract_priorities_from_tasks
from _pytask.dag import descending_tasks
from _pytask.dag import node_and_neighbors
from _pytask.dag import sort_tasks_topologically_w_priorities
from _pytask.dag import task_and_descending_tasks
from _pytask.mark import Mark


@attr.s
class _DummyTask:
    name = attr.ib(type=str, converter=str)
    markers = attr.ib(factory=list)


@pytest.fixture()
def dag():
    dag = nx.DiGraph()
    for i in range(4):
        dag.add_node(str(i), task=_DummyTask(i))
        dag.add_node(str(i + 1), task=_DummyTask(i + 1))
        dag.add_edge(str(i), str(i + 1))

    return dag


@pytest.mark.unit
def test_sort_tasks_topologically(dag):
    tasks = [dag.nodes[node]["task"] for node in dag.nodes]
    topo_ordering = list(sort_tasks_topologically_w_priorities(dag, tasks))
    assert topo_ordering == [str(i) for i in range(5)]


@pytest.mark.unit
def test_descending_tasks(dag):
    for i in range(5):
        descendants = sorted(descending_tasks(str(i), dag))
        assert descendants == [str(i) for i in range(i + 1, 5)]


@pytest.mark.unit
def test_task_and_descending_tasks(dag):
    for i in range(5):
        descendants = sorted(task_and_descending_tasks(str(i), dag))
        assert descendants == [str(i) for i in range(i, 5)]


@pytest.mark.unit
def test_node_and_neighbors(dag):
    for i in range(1, 4):
        nodes = sorted(node_and_neighbors(dag, str(i)))
        assert nodes == [str(j) for j in range(i - 1, i + 2)]


@pytest.mark.unit
@pytest.mark.parametrize(
    "tasks, expectation, expected",
    [
        ([_DummyTask("1", [Mark("try_last", (), {})])], does_not_raise(), {"1": -1}),
        ([_DummyTask("1", [Mark("try_first", (), {})])], does_not_raise(), {"1": 1}),
        ([_DummyTask("1", [])], does_not_raise(), {"1": 0}),
        (
            [_DummyTask("1", [Mark("try_first", (), {}), Mark("try_last", (), {})])],
            pytest.raises(ValueError, match="'try_first' and 'try_last' cannot be"),
            {"1": 1},
        ),
        (
            [
                _DummyTask("1", [Mark("try_first", (), {})]),
                _DummyTask("2", []),
                _DummyTask("3", [Mark("try_last", (), {})]),
            ],
            does_not_raise(),
            {"1": 1, "2": 0, "3": -1},
        ),
    ],
)
def test_extract_priorities_from_tasks(tasks, expectation, expected):
    with expectation:
        result = _extract_priorities_from_tasks(tasks)
        assert result == expected
