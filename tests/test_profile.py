from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest
from _pytask.cli import cli
from _pytask.profile import _to_human_readable_size
from _pytask.profile import Runtime
from pytask import create_database
from pytask import DatabaseSession
from pytask import ExitCode
from pytask import main


@pytest.mark.end_to_end()
def test_duration_is_stored_in_task(tmp_path):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    task = session.tasks[0]
    duration = task.attributes["duration"]
    assert duration[1] - duration[0] > 2

    create_database("sqlite:///" + tmp_path.joinpath(".pytask.sqlite3").as_posix())

    with DatabaseSession() as session:
        task_name = tmp_path.joinpath("task_example.py").as_posix() + "::task_example"

        runtime = session.get(Runtime, task_name)
        assert runtime.duration > 2


@pytest.mark.end_to_end()
def test_profile_if_no_tasks_are_collected(tmp_path, runner):
    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "No information is stored on the collected tasks." in result.output


@pytest.mark.end_to_end()
def test_profile_if_there_is_no_information_on_collected_tasks(tmp_path, runner):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task." in result.output
    assert "No information is stored on the collected tasks." in result.output


@pytest.mark.end_to_end()
def test_profile_if_there_is_information_on_collected_tasks(tmp_path, runner):
    source = """
    import time
    import pytask

    @pytask.mark.produces("out.txt")
    def task_example(produces):
        time.sleep(2)
        produces.write_text("There are nine billion bicycles in Beijing.")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task." in result.output
    assert "Duration (in s)" in result.output
    assert "0." in result.output
    assert "Size of Products" in result.output
    assert "43 bytes" in result.output


@pytest.mark.end_to_end()
@pytest.mark.parametrize("export", ["csv", "json"])
def test_export_of_profile(tmp_path, runner, export):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    cwd = Path.cwd()
    os.chdir(tmp_path)
    result = runner.invoke(cli, ["profile", tmp_path.as_posix(), "--export", export])
    os.chdir(cwd)

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task." in result.output
    assert "Duration (in s)" in result.output
    assert "0." in result.output
    assert tmp_path.joinpath(f"profile.{export}").exists()


@pytest.mark.unit()
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
