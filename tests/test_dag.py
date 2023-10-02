from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from _pytask.dag import pytask_dag_create_dag
from attrs import define
from pytask import build
from pytask import cli
from pytask import ExitCode
from pytask import NodeNotFoundError
from pytask import PathNode
from pytask import Task


@define
class Node(PathNode):
    """See https://github.com/python-attrs/attrs/issues/293 for property hack."""

    def state(self):
        if "missing" in self.name:
            raise NodeNotFoundError


@pytest.mark.unit()
def test_pytask_dag_create_dag():
    root = Path.cwd() / "src"
    task = Task(
        base_name="task_dummy",
        path=root,
        function=None,
        depends_on={
            0: Node.from_path(root / "node_1"),
            1: Node.from_path(root / "node_2"),
        },
    )

    dag = pytask_dag_create_dag([task])

    assert all(
        any(i in node for i in ("node_1", "node_2", "task")) for node in dag.nodes
    )


@pytest.mark.end_to_end()
def test_check_if_root_nodes_are_available(tmp_path, runner):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_d(produces):
        produces.write_text("1")
    """
    tmp_path.joinpath("task_d.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.DAG_FAILED
    assert "Failures during resolving dependencies" in result.output

    # Ensure that node names are reduced.
    assert "Failures during resolving dependencies" in result.output
    assert "Some dependencies do not exist or are" in result.output
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_d" not in result.output
    assert "task_d.py::task_d" in result.output
    assert tmp_path.joinpath("in.txt").as_posix() not in result.output
    assert tmp_path.name + "/in.txt" in result.output


@pytest.mark.end_to_end()
def test_check_if_root_nodes_are_available_w_name(tmp_path, runner):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated, Any
    from pytask import PathNode, PythonNode

    node1 = PathNode(name="input1", path=Path(__file__).parent / "in.txt")
    node2 = PythonNode(name="input2")

    def task_e(in1_: Annotated[Path, node1], in2_: Annotated[Any, node2]): ...
    """
    tmp_path.joinpath("task_e.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.DAG_FAILED
    assert "Failures during resolving dependencies" in result.output

    # Ensure that node names are reduced.
    assert "Failures during resolving dependencies" in result.output
    assert "Some dependencies do not exist or are" in result.output
    assert tmp_path.joinpath("task_e.py").as_posix() + "::task_e" not in result.output
    assert "task_e.py::task_e" in result.output
    assert tmp_path.joinpath("in.txt").as_posix() not in result.output
    assert tmp_path.name + "/in.txt" in result.output


@pytest.mark.end_to_end()
def test_check_if_root_nodes_are_available_with_separate_build_folder(tmp_path, runner):
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

    assert result.exit_code == ExitCode.DAG_FAILED
    assert "Failures during resolving dependencies" in result.output

    # Ensure that node names are reduced.
    assert "Failures during resolving dependencies" in result.output
    assert "Some dependencies do not exist" in result.output
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_d" not in result.output
    assert "task_d.py::task_d" in result.output
    assert tmp_path.joinpath("bld", "in.txt").as_posix() not in result.output
    assert tmp_path.name + "/bld/in.txt" in result.output


@pytest.mark.end_to_end()
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
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.DAG_FAILED
    assert "Failures during resolving dependencies" in result.output
    assert "The DAG contains cycles which means a dependency" in result.output


@pytest.mark.end_to_end()
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

    assert result.exit_code == ExitCode.DAG_FAILED
    assert "Failures during resolving dependencies" in result.output
    assert "There are some tasks which produce the same output." in result.output

    # Ensure that nodes names are reduced.
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_1" not in result.output
    assert "task_d.py::task_1" in result.output
    assert tmp_path.joinpath("task_d.py").as_posix() + "::task_2" not in result.output
    assert "task_d.py::task_2" in result.output
    assert tmp_path.joinpath("out.txt").as_posix() not in result.output
    assert tmp_path.name + "/out.txt" in result.output


@pytest.mark.end_to_end()
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
    assert result.exit_code == ExitCode.OK

    tmp_path.joinpath("file.txt").unlink()

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK


def test_error_when_node_state_throws_error(runner, tmp_path):
    source = """
    from pytask import PythonNode

    def task_example(a = PythonNode(value={"a": 1}, hash=True)):
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.DAG_FAILED
    assert "task_example" in result.output


def test_python_nodes_are_unique(tmp_path):
    tmp_path.joinpath("a").mkdir()
    tmp_path.joinpath("a", "task_example.py").write_text("def task_example(a=1): pass")
    tmp_path.joinpath("b").mkdir()
    tmp_path.joinpath("b", "task_example.py").write_text("def task_example(a=2): pass")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.dag.nodes) == 4
