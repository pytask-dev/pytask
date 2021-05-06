import os
import textwrap

import pytest
from _pytask.cli import cli
from _pytask.database import create_database
from _pytask.profile import Runtime
from pony import orm
from pytask import main


@pytest.mark.end_to_end
def test_duration_is_stored_in_task(tmp_path):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.tasks) == 1
    task = session.tasks[0]
    duration = task.attributes["duration"]
    assert duration[1] - duration[0] > 2

    with orm.db_session:
        create_database(
            "sqlite", tmp_path.joinpath(".pytask.sqlite3").as_posix(), True, False
        )

        task_name = tmp_path.joinpath("task_example.py").as_posix() + "::task_example"

        runtime = Runtime[task_name]
        assert runtime.duration > 2


@pytest.mark.end_to_end
def test_profile_if_no_tasks_are_collected(tmp_path, runner):
    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == 0
    assert "No information is stored on the collected tasks." in result.output


@pytest.mark.end_to_end
def test_profile_if_there_is_no_information_on_collected_tasks(tmp_path, runner):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == 0
    assert "Collected 1 task." in result.output
    assert "No information is stored on the collected tasks." in result.output


@pytest.mark.end_to_end
def test_profile_if_there_is_information_on_collected_tasks(tmp_path, runner):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    result = runner.invoke(cli, ["profile", tmp_path.as_posix()])

    assert result.exit_code == 0
    assert "Collected 1 task." in result.output
    assert "Last Duration (in s)" in result.output
    assert "0." in result.output


@pytest.mark.end_to_end
@pytest.mark.parametrize("export", ["csv", "json"])
def test_export_of_profile(tmp_path, runner, export):
    source = """
    import time
    def task_example(): time.sleep(2)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    os.chdir(tmp_path)
    result = runner.invoke(cli, ["profile", tmp_path.as_posix(), "--export", export])

    assert result.exit_code == 0
    assert "Collected 1 task." in result.output
    assert "Last Duration (in s)" in result.output
    assert "0." in result.output
    assert tmp_path.joinpath(f"profile.{export}").exists()
