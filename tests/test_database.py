from __future__ import annotations

import textwrap

from _pytask.lockfile import build_portable_node_id
from _pytask.lockfile import build_portable_task_id
from _pytask.lockfile import read_lockfile
from _pytask.node_protocols import PNode
from _pytask.tree_util import tree_leaves
from pytask import ExitCode
from pytask import build
from pytask import cli


def test_existence_of_hashes_in_lockfile(tmp_path):
    """Modification dates of input and output files are stored in the lockfile."""
    source = """
    from pathlib import Path

    def task_write(path=Path("in.txt"), produces=Path("out.txt")):
        produces.touch()
    """
    task_path = tmp_path.joinpath("task_module.py")
    task_path.write_text(textwrap.dedent(source))
    in_path = tmp_path.joinpath("in.txt")
    in_path.touch()

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK

    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    tasks_by_id = {entry.id: entry for entry in lockfile.task}

    task = session.tasks[0]
    task_id = build_portable_task_id(task, tmp_path)
    entry = tasks_by_id[task_id]
    assert entry.state == task.state()

    depends_on = task.depends_on
    produces = task.produces
    assert depends_on is not None
    assert produces is not None
    in_nodes = tree_leaves(depends_on["path"])
    out_nodes = tree_leaves(produces["produces"])
    assert len(in_nodes) == 1
    assert len(out_nodes) == 1
    in_node = in_nodes[0]
    out_node = out_nodes[0]
    assert isinstance(in_node, PNode)
    assert isinstance(out_node, PNode)

    in_id = build_portable_node_id(in_node, tmp_path)
    out_id = build_portable_node_id(out_node, tmp_path)
    assert entry.depends_on[in_id] == in_node.state()
    assert entry.produces[out_id] == out_node.state()


def test_rename_database_w_config(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    path_to_db = tmp_path.joinpath(".db.sqlite")
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\ndatabase_url='sqlite:///.db.sqlite'"
    )
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert path_to_db.exists()


def test_rename_database_w_cli(tmp_path, runner):
    """Modification dates of input and output files are stored in database."""
    path_to_db = tmp_path.joinpath(".db.sqlite")
    result = runner.invoke(
        cli,
        ["--database-url", "sqlite:///.db.sqlite", tmp_path.as_posix()],
    )
    assert result.exit_code == ExitCode.OK
    assert path_to_db.exists()
