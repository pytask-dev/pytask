from __future__ import annotations

import subprocess
import textwrap

import pytest
from _pytask.git import init_repo
from pytask import cli
from pytask import ExitCode


@pytest.fixture()
def project(tmp_path):
    """Create a sample project to be cleaned."""
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_write_text(produces):
        produces.write_text("a")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    tmp_path.joinpath("to_be_deleted_file_1.txt").touch()
    tmp_path.joinpath("to_be_deleted_folder_1").mkdir()
    tmp_path.joinpath("to_be_deleted_folder_1", "to_be_deleted_file_2.txt").touch()

    return tmp_path


@pytest.fixture()
def git_project(tmp_path):
    """Create a sample project to be cleaned."""
    source = """
    import pytask

    @pytask.mark.depends_on("in_tracked.txt")
    @pytask.mark.produces("out.txt")
    def task_write_text(produces):
        produces.write_text("a")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_tracked.txt").touch()
    tmp_path.joinpath("tracked.txt").touch()

    init_repo(tmp_path)
    subprocess.run(
        ("git", "add", "task_module.py", "in_tracked.txt", "tracked.txt"), cwd=tmp_path
    )
    subprocess.run(("git", "commit", "-m", "'COMMIT'"), cwd=tmp_path)

    return tmp_path


@pytest.mark.end_to_end
@pytest.mark.parametrize("flag", ["-e", "--exclude"])
@pytest.mark.parametrize("pattern", ["*_1.txt", "to_be_deleted_file_[1]*"])
def test_clean_with_excluded_file(project, runner, flag, pattern):
    result = runner.invoke(cli, ["clean", flag, pattern, project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "to_be_deleted_file_1.txt" not in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks


@pytest.mark.end_to_end
@pytest.mark.parametrize("flag", ["-e", "--exclude"])
def test_clean_with_excluded_directory(project, runner, flag):
    result = runner.invoke(
        cli, ["clean", flag, "to_be_deleted_folder_1/*", project.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert "deleted_folder_1/" not in result.output
    assert "deleted_file_1.txt" in result.output.replace("\n", "")


@pytest.mark.end_to_end
def test_clean_with_nothing_to_remove(tmp_path, runner):
    result = runner.invoke(cli, ["clean", "--exclude", "*", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "There are no files and directories which can be deleted." in result.output


@pytest.mark.end_to_end
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


@pytest.mark.end_to_end
def test_clean_dry_run_w_directories(project, runner):
    result = runner.invoke(cli, ["clean", "-d", project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "Would remove" in text_without_linebreaks
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" not in text_without_linebreaks
    assert "to_be_deleted_folder_1" in text_without_linebreaks


@pytest.mark.end_to_end
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


@pytest.mark.end_to_end
def test_clean_force_w_directories(project, runner):
    result = runner.invoke(cli, ["clean", "-d", "--mode", "force", project.as_posix()])

    assert result.exit_code == ExitCode.OK
    text_without_linebreaks = result.output.replace("\n", "")
    assert "Remove" in text_without_linebreaks
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" not in text_without_linebreaks
    assert "to_be_deleted_folder_1" in text_without_linebreaks


@pytest.mark.end_to_end
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


@pytest.mark.end_to_end
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


@pytest.mark.end_to_end
def test_configuration_failed(runner, tmp_path):
    result = runner.invoke(
        cli, ["clean", tmp_path.joinpath("non_existent_path").as_posix()]
    )
    assert result.exit_code == ExitCode.CONFIGURATION_FAILED


@pytest.mark.end_to_end
def test_collection_failed(runner, tmp_path):
    source = """
    raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["clean", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED


@pytest.mark.end_to_end
def test_dont_remove_files_tracked_by_git(runner, git_project):
    result = runner.invoke(cli, ["clean", git_project.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "tracked.txt" not in result.output
    assert "in_tracked.txt" not in result.output
