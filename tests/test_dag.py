from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest
from _pytask.dag import pytask_dag_create_dag
from pytask import build
from pytask import cli
from pytask import ExitCode
from pytask import PathNode
from pytask import Session
from pytask import Task


@pytest.mark.unit()
@pytest.mark.skipif(sys.platform == "win32", reason="Hashes match only on unix.")
def test_pytask_dag_create_dag():
    root = Path("src")
    task = Task(
        base_name="task_dummy",
        path=root,
        function=None,
        depends_on={
            0: PathNode.from_path(root / "node_1"),
            1: PathNode.from_path(root / "node_2"),
        },
    )
    session = Session.from_config({"paths": (root,)})
    dag = pytask_dag_create_dag(session=session, tasks=[task])

    for signature in (
        "90bb899a1b60da28ff70352cfb9f34a8bed485597c7f40eed9bd4c6449147525",
        "59e9f20637ce34e9bcecc7bafffb5c593bac9388ac3a60d7ed0210444146c705",
        "638a01e495bb8e263036ef2b3009795bb118926cc7f20f005a64c351d820a669",
    ):
        assert signature in dag.nodes


@pytest.mark.end_to_end()
def test_cycle_in_dag(tmp_path, runner, snapshot_cli):
    source = """
    from pathlib import Path

    def task_1(path = Path("out_2.txt"), produces = Path("out_1.txt")):
        produces.write_text("1")

    def task_2(path = Path("out_1.txt"), produces = Path("out_2.txt")):
        produces.write_text("2")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.DAG_FAILED
    if sys.platform == "linux":
        assert result.output == snapshot_cli()


@pytest.mark.end_to_end()
def test_two_tasks_have_the_same_product(tmp_path, runner, snapshot_cli):
    source = """
    from pathlib import Path

    def task_1(produces = Path("out.txt")):
        produces.write_text("1")

    def task_2(produces = Path("out.txt")):
        produces.write_text("2")
    """
    tmp_path.joinpath("task_d.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.DAG_FAILED
    if sys.platform == "linux":
        assert result.output == snapshot_cli()


@pytest.mark.end_to_end()
def test_has_node_changed_catches_notnotfounderror(runner, tmp_path):
    """Missing nodes raise NodeNotFoundError when they do not exist and their state is
    requested."""
    source = """
    from pathlib import Path

    def task_example(produces = Path("file.txt")):
        produces.write_text("test")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    tmp_path.joinpath("file.txt").unlink()

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK


def test_python_nodes_are_unique(tmp_path):
    tmp_path.joinpath("a").mkdir()
    tmp_path.joinpath("a", "task_example.py").write_text("def task_example(a=1): pass")
    tmp_path.joinpath("b").mkdir()
    tmp_path.joinpath("b", "task_example.py").write_text("def task_example(a=2): pass")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.dag.nodes) == 4
