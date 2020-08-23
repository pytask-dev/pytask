import textwrap

import attr
import networkx as nx
import pytest
from _pytask.exceptions import NodeNotFoundError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.resolve_dependencies import _check_if_root_nodes_are_available
from _pytask.resolve_dependencies import pytask_resolve_dependencies_create_dag
from pytask import main


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


@pytest.mark.unit
def test_create_dag():
    task = Task(name="task", depends_on=[Node(name="node_1"), Node(name="node_2")])

    dag = pytask_resolve_dependencies_create_dag([task])

    assert sorted(dag.nodes) == ["node_1", "node_2", "task"]


@pytest.mark.unit
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


@pytest.mark.end_to_end
def test_cycle_in_dag(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.depends_on("out_2.txt")
    @pytask.mark.produces("out_1.txt")
    def task_1(produces):
        produces.write_text("1")

    @pytask.mark.depends_on("out_1.txt")
    @pytask.mark.produces("out_2.txt")
    def task_2(produces):
        produces.write_text("2")
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == 3
    assert isinstance(
        session.resolving_dependencies_report.exc_info[1], ResolvingDependenciesError,
    )
