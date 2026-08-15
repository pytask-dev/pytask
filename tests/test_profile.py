from __future__ import annotations

import csv
import json
import textwrap

import pytest

import _pytask.profile as profile_module
from _pytask.profile import _to_human_readable_size
from _pytask.runtime_store import RuntimeState
from pytask import ExitCode
from pytask import build
from pytask import cli


def test_duration_is_stored_in_task(tmp_path, monkeypatch):
    source = """
    def task_example(): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    times = iter((100.0, 102.25))
    monkeypatch.setattr(profile_module, "_now", lambda: next(times))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    task = session.tasks[0]
    duration = task.attributes["duration"]
    assert duration == (100.0, 102.25)

    runtime_state = RuntimeState.from_root(tmp_path)
    duration = runtime_state.get_duration(task)
    assert duration == pytest.approx(2.25)


def test_profile_if_no_tasks_are_collected(tmp_path, runner):
    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "No information is stored on the collected tasks." in result.output


def test_profile_if_there_is_no_information_on_collected_tasks(tmp_path, runner):
    source = """
    def task_example(): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task." in result.output
    assert "No information is stored on the collected tasks." in result.output


def test_profile_if_there_is_information_on_collected_tasks(tmp_path, runner):
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.write_text("There are nine billion bicycles in Beijing.")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK


@pytest.mark.parametrize("export", ["csv", "json"])
def test_export_of_profile(tmp_path, runner, export):
    source = """
    def task_example(): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    result = runner.invoke(cli, ["profile", tmp_path.as_posix(), "--export", export])

    assert result.exit_code == ExitCode.OK
    export_path = tmp_path.joinpath(f"profile.{export}")
    if export == "csv":
        with export_path.open(newline="") as file:
            rows = list(csv.DictReader(file))
        assert len(rows) == 1
        assert rows[0]["Task"].endswith("task_example")
        assert float(rows[0]["Duration (in s)"]) >= 0
    else:
        profile = json.loads(export_path.read_text())
        assert len(profile) == 1
        task_name, task_profile = next(iter(profile.items()))
        assert task_name.endswith("task_example")
        assert task_profile["Duration (in s)"] >= 0


@pytest.mark.parametrize(
    ("bytes_", "units", "expected"),
    [
        (2**10, None, "1 KB"),
        (2**20, None, "1 MB"),
        (2**30, None, "1 GB"),
        (2**30, [" bytes", " KB", " MB"], "1024 MB"),
    ],
)
def test_to_human_readable_size(bytes_, units, expected):
    result = _to_human_readable_size(bytes_, units)
    assert result == expected
