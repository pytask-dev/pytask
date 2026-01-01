from __future__ import annotations

import textwrap

import pytest

from _pytask.lockfile import LockfileVersionError
from _pytask.lockfile import read_lockfile
from pytask import ExitCode
from pytask import PathNode
from pytask import TaskWithoutPath
from pytask import build


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
