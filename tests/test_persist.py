from __future__ import annotations

import textwrap
from unittest.mock import Mock

import pytest

from _pytask.lockfile import build_portable_node_id
from _pytask.lockfile import build_portable_task_id
from _pytask.lockfile import read_lockfile
from _pytask.persist import pytask_execute_task_process_report
from pytask import ExitCode
from pytask import Persisted
from pytask import SkippedUnchanged
from pytask import TaskOutcome
from pytask import build
from tests.conftest import restore_sys_path_and_module_after_test_execution


def test_persist_marker_is_set(tmp_path):
    session = build(paths=tmp_path)
    assert "persist" in session.config["markers"]


def test_multiple_runs_with_persist(tmp_path):
    """Perform multiple consecutive runs and check intermediate outcomes with persist.

    1. The product is missing which should result in a normal execution of the task.
    2. Change the product, check that run is successful and state in lockfile has
       changed.
    3. Run the task another time. Now, the task is skipped successfully.

    """
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.persist
    def task_dummy(path=Path("in.txt"), produces=Path("out.txt")):
        produces.write_text(path.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("I'm not the reason you care.")

    with restore_sys_path_and_module_after_test_execution():
        session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS
    assert session.execution_reports[0].exc_info is None
    assert tmp_path.joinpath("out.txt").exists()

    tmp_path.joinpath("out.txt").write_text("Never again in despair.")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].outcome == TaskOutcome.PERSISTENCE
    exc_info = session.execution_reports[0].exc_info
    assert exc_info is not None
    assert isinstance(exc_info[1], Persisted)

    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    tasks_by_id = {entry.id: entry for entry in lockfile.task}
    task = session.tasks[0]
    entry = tasks_by_id[build_portable_task_id(task, tmp_path)]
    produces = task.produces
    assert produces is not None
    node = produces["produces"]  # type: ignore[union-attr]
    node_id = build_portable_node_id(node, tmp_path)
    assert entry.produces[node_id] == node.state()

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].outcome == TaskOutcome.SKIP_UNCHANGED
    exc_info2 = session.execution_reports[0].exc_info
    assert exc_info2 is not None
    assert isinstance(exc_info2[1], SkippedUnchanged)


def test_migrating_a_whole_task_with_persist(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.persist
    def task_dummy(depends_on=Path("in.txt"), produces=Path("out.txt")):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    for name in ("in.txt", "out.txt"):
        tmp_path.joinpath(name).write_text(
            "They say oh my god I see the way you shine."
        )

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.execution_reports) == 1
    assert session.execution_reports[0].outcome == TaskOutcome.PERSISTENCE
    exc_info = session.execution_reports[0].exc_info
    assert exc_info is not None
    assert isinstance(exc_info[1], Persisted)


@pytest.mark.parametrize(
    ("exc_info", "expected"),
    [
        (None, None),
        ((None, None, None), None),
        ((None, Persisted(), None), True),
    ],
)
def test_pytask_execute_task_process_report(monkeypatch, exc_info, expected):
    monkeypatch.setattr(
        "_pytask.persist.update_states_in_database",
        lambda *x: None,  # noqa: ARG005
    )

    task = Mock(name=None, signature="id")
    session = Mock(dag=None)
    report = Mock(exc_info=exc_info, task=task)

    result = pytask_execute_task_process_report(session, report)

    if expected:
        assert report.outcome == TaskOutcome.PERSISTENCE
        assert result is True
    else:
        assert result is None
