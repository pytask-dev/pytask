from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest
from _pytask.git import init_repo
from pytask import cli
from pytask import ExitCode


_PROJECT_TASK = """
import pytask

@pytask.mark.depends_on("in.txt")
@pytask.mark.produces("out.txt")
def task_write_text(depends_on, produces):
    produces.write_text("a")
"""


_PROJECT_TASK_NEW_INTERFACE = """
import pytask
from pathlib import Path

def task_write_text(in_path=Path("in.txt"), produces=Path("out.txt")):
    produces.write_text("a")
"""


@pytest.fixture(params=[_PROJECT_TASK, _PROJECT_TASK_NEW_INTERFACE])
def project(request, tmp_path):
    """Create a sample project to be cleaned."""
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(request.param))
    tmp_path.joinpath("in.txt").touch()

    tmp_path.joinpath("to_be_deleted_file_1.txt").touch()
    tmp_path.joinpath("to_be_deleted_folder_1").mkdir()
    tmp_path.joinpath("to_be_deleted_folder_1", "to_be_deleted_file_2.txt").touch()

    return tmp_path


_GIT_PROJECT_TASK = """
import pytask

@pytask.mark.depends_on("in_tracked.txt")
@pytask.mark.produces("out.txt")
def task_write_text(depends_on, produces):
    produces.write_text("a")
"""


_GIT_PROJECT_TASK_NEW_INTERFACE = """
import pytask
from pathlib import Path

def task_write_text(in_path=Path("in_tracked.txt"), produces=Path("out.txt")):
    produces.write_text("a")
"""


@pytest.fixture(params=[_GIT_PROJECT_TASK, _GIT_PROJECT_TASK_NEW_INTERFACE])
def git_project(request, tmp_path):
    """Create a sample project to be cleaned."""
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(request.param))
    tmp_path.joinpath("in_tracked.txt").touch()
    tmp_path.joinpath("tracked.txt").touch()

    init_repo(tmp_path)
    subprocess.run(
        ("git", "add", "task_module.py", "in_tracked.txt", "tracked.txt"), cwd=tmp_path
    )
    subprocess.run(("git", "commit", "-m", "'COMMIT'"), cwd=tmp_path)

    return tmp_path


@pytest.mark.end_to_end()
def test_clean_database_ignored(project, runner):
    cwd = Path.cwd()
    os.chdir(project)
    result = runner.invoke(cli, ["build"])
    assert result.exit_code == ExitCode.OK
    result = runner.invoke(cli, ["clean"])
    assert result.exit_code == ExitCode.OK
    os.chdir(cwd)

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks
    assert ".pytask.sqlite3" not in text_without_linebreaks


@pytest.mark.end_to_end()
def test_clean_with_auto_collect(project, runner):
    cwd = Path.cwd()
    os.chdir(project)
    result = runner.invoke(cli, ["clean"])
    assert result.exit_code == ExitCode.OK
    os.chdir(cwd)

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks


@pytest.mark.end_to_end()
@pytest.mark.parametrize("flag", ["-e", "--exclude"])
@pytest.mark.parametrize("pattern", ["*_1.txt", "to_be_deleted_file_[1]*"])
def test_clean_with_excluded_file(project, runner, flag, pattern):
    result = runner.invoke(cli, ["clean", flag, pattern, project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "to_be_deleted_file_1.txt" not in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks


@pytest.mark.end_to_end()
@pytest.mark.parametrize("flag", ["-e", "--exclude"])
@pytest.mark.parametrize("pattern", ["*_1.txt", "to_be_deleted_file_[1]*"])
def test_clean_with_excluded_file_via_config(project, runner, flag, pattern):
    project.joinpath("pyproject.toml").write_text(
        f"[tool.pytask.ini_options]\nexclude = [{pattern!r}]"
    )

    result = runner.invoke(cli, ["clean", flag, pattern, project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "to_be_deleted_file_1.txt" not in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks
    assert "pyproject.toml" in text_without_linebreaks


@pytest.mark.end_to_end()
@pytest.mark.parametrize("flag", ["-e", "--exclude"])
def test_clean_with_excluded_directory(project, runner, flag):
    result = runner.invoke(
        cli, ["clean", flag, "to_be_deleted_folder_1/*", project.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert "deleted_folder_1/" not in result.output
    assert "deleted_file_1.txt" in result.output.replace("\n", "")


@pytest.mark.end_to_end()
def test_clean_with_nothing_to_remove(tmp_path, runner):
    result = runner.invoke(cli, ["clean", "--exclude", "*", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "There are no files and directories which can be deleted." in result.output


@pytest.mark.end_to_end()
def test_clean_dry_run(project, runner):
    result = runner.invoke(cli, ["clean", project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "Would remove" in text_without_linebreaks
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert project.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks
    assert project.joinpath(
        "to_be_deleted_folder_1", "to_be_deleted_file_2.txt"
    ).exists()


@pytest.mark.end_to_end()
def test_clean_dry_run_w_directories(project, runner):
    result = runner.invoke(cli, ["clean", "-d", project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "Would remove" in text_without_linebreaks
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" not in text_without_linebreaks
    assert "to_be_deleted_folder_1" in text_without_linebreaks


@pytest.mark.end_to_end()
def test_clean_force(project, runner):
    result = runner.invoke(cli, ["clean", "--mode", "force", project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "Remove" in result.output
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert not project.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks
    assert not project.joinpath(
        "to_be_deleted_folder_1", "to_be_deleted_file_2.txt"
    ).exists()


@pytest.mark.end_to_end()
def test_clean_force_w_directories(project, runner):
    result = runner.invoke(cli, ["clean", "-d", "--mode", "force", project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "Remove" in text_without_linebreaks
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" not in text_without_linebreaks
    assert "to_be_deleted_folder_1" in text_without_linebreaks


@pytest.mark.end_to_end()
def test_clean_interactive(project, runner):
    result = runner.invoke(
        cli,
        ["clean", "--mode", "interactive", project.as_posix()],
        # Three instead of two because the compiled .pyc file is also present.
        input="y\ny\ny",
    )

    assert result.exit_code == ExitCode.OK
    assert "Remove" in result.output
    assert "to_be_deleted_file_1.txt" in result.output
    assert not project.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" in result.output
    assert not project.joinpath(
        "to_be_deleted_folder_1", "to_be_deleted_file_2.txt"
    ).exists()


@pytest.mark.end_to_end()
def test_clean_interactive_w_directories(project, runner):
    result = runner.invoke(
        cli,
        ["clean", "-d", "--mode", "interactive", project.as_posix()],
        # Three instead of two because the compiled .pyc file is also present.
        input="y\ny\ny",
    )

    assert result.exit_code == ExitCode.OK
    assert "Remove" in result.output
    assert "to_be_deleted_file_1.txt" in result.output
    assert not project.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" not in result.output
    assert "to_be_deleted_folder_1" in result.output
    assert not project.joinpath("to_be_deleted_folder_1").exists()


@pytest.mark.end_to_end()
def test_configuration_failed(runner, tmp_path):
    result = runner.invoke(
        cli, ["clean", tmp_path.joinpath("non_existent_path").as_posix()]
    )
    assert result.exit_code == ExitCode.CONFIGURATION_FAILED


@pytest.mark.end_to_end()
def test_collection_failed(runner, tmp_path):
    source = """
    raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["clean", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED


@pytest.mark.end_to_end()
def test_dont_remove_files_tracked_by_git(runner, git_project):
    result = runner.invoke(cli, ["clean", git_project.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "tracked.txt" not in result.output
    assert "in_tracked.txt" not in result.output
    assert ".git" not in result.output


@pytest.mark.end_to_end()
def test_clean_git_files_if_git_is_not_installed(monkeypatch, runner, git_project):
    monkeypatch.setattr(
        "_pytask.clean.is_git_installed", lambda *x: False  # noqa: ARG005
    )

    result = runner.invoke(cli, ["clean", git_project.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "tracked.txt" in result.output
    assert "in_tracked.txt" not in result.output
    assert ".git" not in result.output


@pytest.mark.end_to_end()
def test_clean_git_files_if_git_is_installed_but_git_root_is_not_found(
    monkeypatch, runner, git_project
):
    monkeypatch.setattr("_pytask.clean.get_root", lambda x: None)  # noqa: ARG005

    result = runner.invoke(cli, ["clean", git_project.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "tracked.txt" in result.output
    assert "in_tracked.txt" not in result.output
    assert ".git" not in result.output
