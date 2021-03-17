import textwrap

import pytest
from pytask import cli


@pytest.fixture()
def sample_project_path(tmp_path):
    """Create a sample project to be cleaned."""
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(produces):
        produces.write_text("a")
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    tmp_path.joinpath("to_be_deleted_file_1.txt").touch()
    tmp_path.joinpath("to_be_deleted_folder_1").mkdir()
    tmp_path.joinpath("to_be_deleted_folder_1", "to_be_deleted_file_2.txt").touch()

    return tmp_path


@pytest.mark.end_to_end
def test_clean_with_ignored_file(sample_project_path, runner):
    result = runner.invoke(
        cli, ["clean", "--ignore", "*_1.txt", sample_project_path.as_posix()]
    )

    text_without_linebreaks = result.output.replace("\n", "")
    assert "to_be_deleted_file_1.txt" not in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" in text_without_linebreaks


@pytest.mark.end_to_end
def test_clean_with_ingored_directory(sample_project_path, runner):
    result = runner.invoke(
        cli,
        [
            "clean",
            "--ignore",
            "to_be_deleted_folder_1/*",
            sample_project_path.as_posix(),
        ],
    )

    assert "to_be_deleted_folder_1/" not in result.output
    assert "to_be_deleted_file_1.txt" in result.output.replace("\n", "")


@pytest.mark.end_to_end
def test_clean_with_nothing_to_remove(tmp_path, runner):
    result = runner.invoke(cli, ["clean", "--ignore", "*", tmp_path.as_posix()])

    assert "There are no files and directories which can be deleted." in result.output


@pytest.mark.end_to_end
def test_clean_dry_run(sample_project_path, runner):
    result = runner.invoke(cli, ["clean", sample_project_path.as_posix()])

    assert "Would remove" in result.output
    assert "to_be_deleted_file_1.txt" in result.output
    assert sample_project_path.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" in result.output
    assert sample_project_path.joinpath(
        "to_be_deleted_folder_1", "to_be_deleted_file_2.txt"
    ).exists()


@pytest.mark.end_to_end
def test_clean_dry_run_w_directories(sample_project_path, runner):
    result = runner.invoke(cli, ["clean", "-d", sample_project_path.as_posix()])

    text_without_linebreaks = result.output.replace("\n", "")
    assert "Would remove" in text_without_linebreaks
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" not in text_without_linebreaks
    assert "to_be_deleted_folder_1" in text_without_linebreaks


@pytest.mark.end_to_end
def test_clean_force(sample_project_path, runner):
    result = runner.invoke(
        cli, ["clean", "--mode", "force", sample_project_path.as_posix()]
    )

    assert "Remove" in result.output
    assert "to_be_deleted_file_1.txt" in result.output
    assert not sample_project_path.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" in result.output
    assert not sample_project_path.joinpath(
        "to_be_deleted_folder_1", "to_be_deleted_file_2.txt"
    ).exists()


@pytest.mark.end_to_end
def test_clean_force_w_directories(sample_project_path, runner):
    result = runner.invoke(
        cli, ["clean", "-d", "--mode", "force", sample_project_path.as_posix()]
    )

    text_without_linebreaks = result.output.replace("\n", "")
    assert "Remove" in text_without_linebreaks
    assert "to_be_deleted_file_1.txt" in text_without_linebreaks
    assert "to_be_deleted_file_2.txt" not in text_without_linebreaks
    assert "to_be_deleted_folder_1" in text_without_linebreaks


@pytest.mark.end_to_end
def test_clean_interactive(sample_project_path, runner):
    result = runner.invoke(
        cli,
        ["clean", "--mode", "interactive", sample_project_path.as_posix()],
        # Three instead of two because the compiled .pyc file is also present.
        input="y\ny\ny",
    )

    assert "Remove" in result.output
    assert "to_be_deleted_file_1.txt" in result.output
    assert not sample_project_path.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" in result.output
    assert not sample_project_path.joinpath(
        "to_be_deleted_folder_1", "to_be_deleted_file_2.txt"
    ).exists()


@pytest.mark.end_to_end
def test_clean_interactive_w_directories(sample_project_path, runner):
    result = runner.invoke(
        cli,
        ["clean", "-d", "--mode", "interactive", sample_project_path.as_posix()],
        # Three instead of two because the compiled .pyc file is also present.
        input="y\ny\ny",
    )

    assert "Remove" in result.output
    assert "to_be_deleted_file_1.txt" in result.output
    assert not sample_project_path.joinpath("to_be_deleted_file_1.txt").exists()
    assert "to_be_deleted_file_2.txt" not in result.output
    assert "to_be_deleted_folder_1" in result.output
    assert not sample_project_path.joinpath("to_be_deleted_folder_1").exists()


@pytest.mark.end_to_end
def test_configuration_failed(runner, tmp_path):
    result = runner.invoke(
        cli, ["clean", tmp_path.joinpath("non_existent_path").as_posix()]
    )
    assert result.exit_code == 2


@pytest.mark.end_to_end
def test_collection_failed(runner, tmp_path):
    source = """
    raise Exception
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["clean", tmp_path.as_posix()])
    assert result.exit_code == 3
