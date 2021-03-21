import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import attr
import networkx as nx
import pytest
from _pytask.exceptions import NodeNotFoundError
from _pytask.exceptions import ResolvingDependenciesError
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.resolve_dependencies import _check_if_root_nodes_are_available
from _pytask.resolve_dependencies import pytask_resolve_dependencies_create_dag
from pytask import cli


@attr.s
class Task(MetaTask):
    name = attr.ib(type=str)
    depends_on = attr.ib(factory=dict)
    produces = attr.ib(factory=dict)

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


class DummySession:
    pass


@pytest.mark.unit
def test_create_dag():
    task = Task(
        name="task",
        depends_on={0: Node(name="node_1"), 1: Node(name="node_2")},
    )

    dag = pytask_resolve_dependencies_create_dag([task])

    assert sorted(dag.nodes) == ["node_1", "node_2", "task"]


@pytest.mark.unit
def test_check_if_root_nodes_are_available():
    dag = nx.DiGraph()

    root = Path("directory")
    session = DummySession()
    session.config = {"paths": [root]}

    task = Task("task")
    task.path = root.joinpath("task_dummy")
    task.base_name = "task_dummy"
    dag.add_node(task.name, task=task)

    available_node = Node("available")
    available_node.path = root.joinpath("available_node")
    dag.add_node(available_node.name, node=available_node)
    dag.add_edge(available_node.name, task.name)

    with does_not_raise():
        _check_if_root_nodes_are_available(dag, session)

    missing_node = Node("missing")
    missing_node.path = root.joinpath("missing_node")
    dag.add_node(missing_node.name, node=missing_node)
    dag.add_edge(missing_node.name, task.name)

    with pytest.raises(ResolvingDependenciesError):
        _check_if_root_nodes_are_available(dag, session)


@pytest.mark.end_to_end
def test_check_if_root_nodes_are_available_end_to_end(tmp_path, runner):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_d(produces):
        produces.write_text("1")
    """
    tmp_path.joinpath("task_d.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 4
    assert "Failures during resolving dependencies" in result.output

    # Ensure that node names are reduced.
    assert "Failures during resolving dependencies" in result.output
    assert "There are some dependencies missing which do not" in result.output
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_d" not in result.output
    assert tmp_path.name + "/task_d.py::task_d" in result.output
    assert tmp_path.joinpath("in.txt").as_posix() not in result.output
    assert tmp_path.name + "/in.txt" in result.output


@pytest.mark.end_to_end
def test_check_if_root_nodes_are_available_with_separate_build_folder_end_to_end(
    tmp_path, runner
):
    tmp_path.joinpath("src").mkdir()
    tmp_path.joinpath("bld").mkdir()
    source = """
    import pytask

    @pytask.mark.depends_on("../bld/in.txt")
    @pytask.mark.produces("out.txt")
    def task_d(produces):
        produces.write_text("1")
    """
    tmp_path.joinpath("src", "task_d.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.joinpath("src").as_posix()])

    assert result.exit_code == 4
    assert "Failures during resolving dependencies" in result.output

    # Ensure that node names are reduced.
    assert "Failures during resolving dependencies" in result.output
    assert "There are some dependencies missing which do not" in result.output
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_d" not in result.output
    assert "src/task_d.py::task_d" in result.output
    assert tmp_path.joinpath("bld", "in.txt").as_posix() not in result.output
    assert tmp_path.name + "/bld/in.txt" in result.output


@pytest.mark.end_to_end
def test_cycle_in_dag(tmp_path, runner):
    source = """
    import pytask

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

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 4
    assert "Failures during resolving dependencies" in result.output
    assert "The DAG contains cycles which means a dependency" in result.output


@pytest.mark.end_to_end
def test_two_tasks_have_the_same_product(tmp_path, runner):
    source = """
    import pytask

    @pytask.mark.produces("out.txt")
    def task_1(produces):
        produces.write_text("1")

    @pytask.mark.produces("out.txt")
    def task_2(produces):
        produces.write_text("2")
    """
    tmp_path.joinpath("task_d.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 4
    assert "Failures during resolving dependencies" in result.output
    assert "There are some tasks which produce the same output." in result.output

    # Ensure that nodes names are reduced.
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_1" not in result.output
    assert tmp_path.name + "/task_d.py::task_1" in result.output
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_2" not in result.output
    assert tmp_path.name + "/task_d.py::task_2" in result.output
    assert tmp_path.joinpath("out.txt").as_posix() not in result.output
    assert tmp_path.name + "/out.txt" in result.output


@pytest.mark.end_to_end
def test_has_node_changed_catches_notnotfounderror(runner, tmp_path):
    """Missing nodes raise NodeNotFoundError when they do not exist and their state is
    requested."""
    source = """
    import pytask

    @pytask.mark.produces("file.txt")
    def task_example(produces):
        produces.write_text("test")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == 0

    tmp_path.joinpath("file.txt").unlink()

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == 0
