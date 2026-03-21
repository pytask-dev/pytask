from __future__ import annotations

import textwrap

import pytest

import _pytask.lockfile as lockfile_module
from _pytask.lockfile import LockfileError
from _pytask.lockfile import LockfileVersionError
from _pytask.lockfile import build_portable_node_id
from _pytask.lockfile import read_lockfile
from _pytask.models import NodeInfo
from _pytask.nodes import PythonNode
from pytask import DatabaseSession
from pytask import ExitCode
from pytask import PathNode
from pytask import State
from pytask import TaskWithoutPath
from pytask import build
from pytask import cli


def test_lockfile_rejects_older_version(tmp_path):
    path = tmp_path / "pytask.lock"
    path.write_text(
        textwrap.dedent(
            """
            lock-version = "0.9"
            task = []
            """
        ).strip()
        + "\n"
    )

    with pytest.raises(LockfileVersionError):
        read_lockfile(path)


def test_lockfile_rejects_newer_version(tmp_path):
    path = tmp_path / "pytask.lock"
    path.write_text(
        textwrap.dedent(
            """
            lock-version = "9.0"
            task = []
            """
        ).strip()
        + "\n"
    )

    with pytest.raises(LockfileVersionError):
        read_lockfile(path)


def test_lockfile_rejects_invalid_version_string(tmp_path):
    path = tmp_path / "pytask.lock"
    path.write_text(
        textwrap.dedent(
            """
            lock-version = "abc"
            task = []
            """
        ).strip()
        + "\n"
    )

    with pytest.raises(LockfileVersionError, match=r"Invalid lock-version"):
        read_lockfile(path)


def test_lockfile_rejects_invalid_format(tmp_path):
    path = tmp_path / "pytask.lock"
    path.write_text("{not toml")

    with pytest.raises(LockfileError):
        read_lockfile(path)


def test_python_node_id_is_collision_free(tmp_path):
    task_path = tmp_path / "task.py"
    node_info_left = NodeInfo(
        arg_name="value",
        path=("a-b", "c"),
        task_path=task_path,
        task_name="task",
        value=None,
    )
    node_info_right = NodeInfo(
        arg_name="value",
        path=("a", "b-c"),
        task_path=task_path,
        task_name="task",
        value=None,
    )
    node_left = PythonNode(name="node", value=1, node_info=node_info_left)
    node_right = PythonNode(name="node", value=1, node_info=node_info_right)

    left_id = build_portable_node_id(node_left, tmp_path)
    right_id = build_portable_node_id(node_right, tmp_path)
    assert left_id != right_id


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(lambda path: [path.as_posix()], id="build"),
        pytest.param(lambda path: ["collect", path.as_posix()], id="collect"),
    ],
)
def test_collection_fails_for_ambiguous_lockfile_ids(runner, tmp_path, args):
    source = """
    from dataclasses import dataclass, field
    from pathlib import Path
    from typing import Any

    @dataclass
    class CustomNode:
        name: str
        value: str
        signature: str
        attributes: dict[Any, Any] = field(default_factory=dict)

        def state(self):
            return self.value

        def load(self, is_product=False):
            return self.value

        def save(self, value):
            self.value = value

    def task_example(
        first=CustomNode(name="dup", value="1", signature="signature-a"),
        second=CustomNode(name="dup", value="2", signature="signature-b"),
        produces=Path("out.txt"),
    ):
        produces.write_text(first + second)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, args(tmp_path))

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Ambiguous lockfile ids detected" in result.output
    assert "lockfile id 'dup'" in result.output


def test_markers_command_ignores_invalid_lockfile(runner, tmp_path):
    tmp_path.joinpath("pytask.lock").write_text("{not toml")

    result = runner.invoke(cli, ["markers", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "persist" in result.output


def test_collection_fails_for_ambiguous_lockfile_ids_with_missing_product_state(
    runner, tmp_path
):
    source = """
    from dataclasses import dataclass, field
    from pathlib import Path
    from typing import Annotated, Any

    from pytask import Product

    @dataclass
    class CustomNode:
        name: str
        filepath: Path
        signature: str
        attributes: dict[Any, Any] = field(default_factory=dict)

        def state(self):
            if not self.filepath.exists():
                return None
            return self.filepath.read_text()

        def load(self, is_product=False):
            return self if is_product else self.filepath.read_text()

        def save(self, value):
            self.filepath.write_text(value)

    def task_example(
        dependency=CustomNode(
            name="dup", filepath=Path("in.txt"), signature="signature-a"
        ),
        product: Annotated[CustomNode, Product] = CustomNode(
            name="dup", filepath=Path("out.txt"), signature="signature-b"
        ),
    ):
        product.save(dependency.upper())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("hello")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Ambiguous lockfile ids detected" in result.output
    assert "lockfile id 'dup'" in result.output


def test_lockfile_writes_state_to_database_for_compatibility(tmp_path):
    def func(path):
        path.write_text("data")

    task = TaskWithoutPath(
        name="task",
        function=func,
        produces={"path": PathNode(path=tmp_path / "out.txt")},
    )

    session = build(tasks=[task], paths=tmp_path)
    assert session.exit_code == ExitCode.OK
    assert (tmp_path / "pytask.lock").exists()

    db_path = tmp_path / ".pytask" / "pytask.sqlite3"
    assert db_path.exists()

    task_signature = session.tasks[0].signature
    with DatabaseSession() as db_session:
        state = db_session.get(State, (task_signature, task_signature))
    assert state is not None
    assert state.hash_ == session.tasks[0].state()


def test_clean_lockfile_removes_stale_entries(tmp_path):
    def func_first(path):
        path.touch()

    def func_second(path):
        path.touch()

    task_first = TaskWithoutPath(
        name="task_first",
        function=func_first,
        produces={"path": PathNode(path=tmp_path / "first.txt")},
    )
    task_second = TaskWithoutPath(
        name="task_second",
        function=func_second,
        produces={"path": PathNode(path=tmp_path / "second.txt")},
    )

    session = build(tasks=[task_first, task_second], paths=tmp_path)
    assert session.exit_code == ExitCode.OK
    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    assert {entry.id for entry in lockfile.task} == {"task_first", "task_second"}

    session = build(tasks=[task_first], paths=tmp_path, clean_lockfile=True)
    assert session.exit_code == ExitCode.OK
    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    assert {entry.id for entry in lockfile.task} == {"task_first"}


def test_update_task_skips_write_when_unchanged(tmp_path, monkeypatch):
    def func(path):
        path.write_text("data")

    task = TaskWithoutPath(
        name="task",
        function=func,
        produces={"path": PathNode(path=tmp_path / "out.txt")},
    )

    session = build(tasks=[task], paths=tmp_path)
    assert session.exit_code == ExitCode.OK

    lockfile_state = session.config["lockfile_state"]
    assert lockfile_state is not None

    calls = {"count": 0}

    original_append = lockfile_module.JsonlJournal.append

    def _counting_append(self, payload):
        calls["count"] += 1
        return original_append(self, payload)

    monkeypatch.setattr(lockfile_module.JsonlJournal, "append", _counting_append)
    lockfile_state.update_task(session, session.tasks[0])

    assert calls["count"] == 0


def test_update_task_appends_journal_on_change(tmp_path):
    def func(path):
        path.write_text("data")

    task = TaskWithoutPath(
        name="task",
        function=func,
        produces={"path": PathNode(path=tmp_path / "out.txt")},
    )

    session = build(tasks=[task], paths=tmp_path)
    assert session.exit_code == ExitCode.OK

    lockfile_state = session.config["lockfile_state"]
    assert lockfile_state is not None

    def new_func(path):
        path.write_text("changed")

    session.tasks[0].function = new_func

    lockfile_state.update_task(session, session.tasks[0])

    journal_path = (tmp_path / "pytask.lock").with_suffix(".lock.journal")
    assert journal_path.exists()
    assert journal_path.read_text().strip()


def test_journal_replay_updates_lockfile_state(tmp_path):
    def func(path):
        path.write_text("data")

    task = TaskWithoutPath(
        name="task",
        function=func,
        produces={"path": PathNode(path=tmp_path / "out.txt")},
    )

    session = build(tasks=[task], paths=tmp_path)
    assert session.exit_code == ExitCode.OK

    lockfile_state = session.config["lockfile_state"]
    assert lockfile_state is not None

    def new_func(path):
        path.write_text("changed")

    session.tasks[0].function = new_func
    lockfile_state.update_task(session, session.tasks[0])

    journal_path = (tmp_path / "pytask.lock").with_suffix(".lock.journal")
    assert journal_path.exists()

    reloaded = lockfile_module.LockfileState.from_path(
        tmp_path / "pytask.lock", tmp_path
    )
    entry = reloaded.get_task_entry("task")
    assert entry is not None
    assert entry.state == session.tasks[0].state()


def test_flush_writes_lockfile_and_deletes_journal(tmp_path):
    def func(path):
        path.write_text("data")

    task = TaskWithoutPath(
        name="task",
        function=func,
        produces={"path": PathNode(path=tmp_path / "out.txt")},
    )

    session = build(tasks=[task], paths=tmp_path)
    assert session.exit_code == ExitCode.OK

    lockfile_state = session.config["lockfile_state"]
    assert lockfile_state is not None

    def new_func(path):
        path.write_text("changed")

    session.tasks[0].function = new_func
    lockfile_state.update_task(session, session.tasks[0])

    journal_path = (tmp_path / "pytask.lock").with_suffix(".lock.journal")
    assert journal_path.exists()

    lockfile_state.flush()

    assert not journal_path.exists()
    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    entries = {entry.id: entry for entry in lockfile.task}
    assert entries["task"].state == session.tasks[0].state()
