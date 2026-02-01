from __future__ import annotations

from types import SimpleNamespace

import pytest

from _pytask.runtime_store import RuntimeState


def test_runtime_state_recovers_from_journal(tmp_path):
    tmp_path.joinpath(".pytask").mkdir()
    task = SimpleNamespace(name="task_example")

    state = RuntimeState.from_root(tmp_path)
    state.update_task(task, 1.0, 3.0)

    recovered = RuntimeState.from_root(tmp_path)
    assert recovered.get_duration(task) == pytest.approx(2.0)


def test_runtime_state_flushes_journal(tmp_path):
    tmp_path.joinpath(".pytask").mkdir()
    task = SimpleNamespace(name="task_example")

    state = RuntimeState.from_root(tmp_path)
    state.update_task(task, 2.0, 5.5)

    journal_path = tmp_path / ".pytask" / "runtimes.journal"
    runtimes_path = tmp_path / ".pytask" / "runtimes.json"
    assert journal_path.exists()

    state.flush()

    assert not journal_path.exists()
    assert runtimes_path.exists()

    reloaded = RuntimeState.from_root(tmp_path)
    assert reloaded.get_duration(task) == pytest.approx(3.5)
