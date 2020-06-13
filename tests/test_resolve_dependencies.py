import attr
import networkx as nx
import pytest
from pytask.exceptions import NodeNotFoundError
from pytask.nodes import MetaNode
from pytask.nodes import MetaTask
from pytask.resolve_dependencies import _check_if_root_nodes_are_available
from pytask.resolve_dependencies import pytask_resolve_dependencies_create_dag


@attr.s
class Task(MetaTask):
    name = attr.ib(type=str)
    depends_on = attr.ib(default=[])
    produces = attr.ib(default=[])

    def execute(self):
        pass

    def state(self):
        pass


@attr.s
class Node(MetaNode):
    """See https://github.com/python-attrs/attrs/issues/293 for property hack."""

    name = attr.ib(type=str)

    def state(self):
        if self.name == "missing":
            raise NodeNotFoundError


def test_create_dag():
    task = Task(name="task", depends_on=[Node(name="node_1"), Node(name="node_2")])

    dag = pytask_resolve_dependencies_create_dag([task])

    assert sorted(dag.nodes) == ["node_1", "node_2", "task"]


def test_check_if_root_nodes_are_available():
    dag = nx.DiGraph()

    task = Task("task")
    dag.add_node(task.name, task=task)

    available_node = Node("available")
    dag.add_node(available_node.name, node=available_node)
    dag.add_edge(available_node.name, task.name)

    _check_if_root_nodes_are_available(dag)

    missing_node = Node("missing")
    dag.add_node(missing_node.name, node=missing_node)
    dag.add_edge(missing_node.name, task.name)

    with pytest.raises(NodeNotFoundError):
        _check_if_root_nodes_are_available(dag)
