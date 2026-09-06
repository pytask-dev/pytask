from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pytask import ExitCode
from pytask import build
from pytask import cli
from tests.conftest import enter_directory


def test_debug_pytask(capsys, tmp_path):
    session = build(paths=tmp_path, debug_pytask=True)

    assert session.exit_code == ExitCode.OK

    captured = capsys.readouterr()

    # The first hooks which will be displayed.
    assert "pytask_post_parse [hook]" in captured.out
    assert "finish pytask_post_parse --> [] [hook]" in captured.out
    # The last hooks which will be displayed.
    assert "finish pytask_execute_log_end --> [True] [hook]" in captured.out
    assert "finish pytask_execute --> None [hook]" in captured.out


def test_pass_config_to_cli(tmp_path):
    config = """
    [tool.pytask.ini_options]
    markers = {"elton" = "Can you feel the love tonight?"}
    """
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(config))

    session = build(config=tmp_path.joinpath("pyproject.toml"), paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert "elton" in session.config["markers"]


@pytest.mark.parametrize(
    "file_or_folder",
    ["folder_a", "folder_a/task_a.py", "folder_b", "folder_b/task_b.py"],
)
def test_passing_paths_via_configuration_file(tmp_path, file_or_folder):
    config = f"""
    [tool.pytask.ini_options]
    paths = ["{file_or_folder}"]
    """
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(config))

    for letter in ("a", "b"):
        tmp_path.joinpath(f"folder_{letter}").mkdir()
        tmp_path.joinpath(f"folder_{letter}", f"task_{letter}.py").write_text(
            "def task_passes(): pass"
        )

    session = build(config=tmp_path.joinpath("pyproject.toml"))

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1


def test_not_existing_path_in_config(runner, tmp_path):
    config = """
    [tool.pytask.ini_options]
    paths = ["not_existing_path"]
    """
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(config))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.CONFIGURATION_FAILED


def test_paths_are_relative_to_configuration_file_cli(tmp_path, runner):
    tmp_path.joinpath("src").mkdir()
    tmp_path.joinpath("tasks").mkdir()
    config = """
    [tool.pytask.ini_options]
    paths = ["../tasks"]
    """
    tmp_path.joinpath("src", "pyproject.toml").write_text(textwrap.dedent(config))

    source = "def task_example(): ..."
    tmp_path.joinpath("tasks", "task_example.py").write_text(source)

    with enter_directory(tmp_path):
        result = runner.invoke(cli, ["src"])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


def test_paths_are_relative_to_configuration_file(tmp_path):
    tmp_path.joinpath("src").mkdir()
    tmp_path.joinpath("tasks").mkdir()
    config = """
    [tool.pytask.ini_options]
    paths = ["../tasks"]
    """
    tmp_path.joinpath("src", "pyproject.toml").write_text(textwrap.dedent(config))

    source = "def task_example(): ..."
    tmp_path.joinpath("tasks", "task_example.py").write_text(source)

    with enter_directory(tmp_path):
        session = build(paths=[Path("src")])

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1


def test_create_gitignore_file_in_pytask_directory(tmp_path):
    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert tmp_path.joinpath(".pytask", ".gitignore").exists()
