import networkx as nx
import pytest
from _pytask.dag import descending_tasks
from _pytask.dag import node_and_neighbors
from _pytask.dag import sort_tasks_topologically
from _pytask.dag import task_and_descending_tasks


@pytest.fixture()
def dag():
    dag = nx.DiGraph()
    for i in range(4):
        dag.add_node(str(i), task=None)
        dag.add_node(str(i + 1), task=None)
        dag.add_edge(str(i), str(i + 1))

    return dag


def test_sort_tasks_topologically(dag):
    topo_ordering = list(sort_tasks_topologically(dag))
    assert topo_ordering == [str(i) for i in range(5)]


def test_descending_tasks(dag):
    for i in range(5):
        descendants = sorted(descending_tasks(str(i), dag))
        assert descendants == [str(i) for i in range(i + 1, 5)]


def test_task_and_descending_tasks(dag):
    for i in range(5):
        descendants = sorted(task_and_descending_tasks(str(i), dag))
        assert descendants == [str(i) for i in range(i, 5)]


def test_node_and_neighbors(dag):
    for i in range(1, 4):
        nodes = sorted(node_and_neighbors(dag, str(i)))
        assert nodes == [str(j) for j in range(i - 1, i + 2)]
