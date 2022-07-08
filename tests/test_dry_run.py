from __future__ import annotations

import textwrap

import pytest
from pytask import cli
from pytask import ExitCode


@pytest.mark.end_to_end
def test_dry_run(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Would be executed" in result.output
    assert not tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end
def test_dry_run_w_subsequent_task(runner, tmp_path):
    """Subsequent tasks would be executed if their previous task changed."""
    source = """
    import pytask

    @pytask.mark.depends_on("out.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example_second.py").write_text(textwrap.dedent(source))

    source = """
    import pytask

    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example_first.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output

    tmp_path.joinpath("task_example_first.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Would be executed" in result.output


@pytest.mark.end_to_end
def test_dry_run_w_subsequent_skipped_task(runner, tmp_path):
    """A skip is more important than a would be run."""
    source = """
    import pytask

    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example_first.py").write_text(textwrap.dedent(source))

    source = """
    import pytask

    @pytask.mark.depends_on("out.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example_second.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output

    source = """
    import pytask

    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example_first.py").write_text(textwrap.dedent(source))

    source = """
    import pytask

    @pytask.mark.skip
    @pytask.mark.depends_on("out.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example_second.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Would be executed" in result.output
    assert "1  Skipped" in result.output


@pytest.mark.end_to_end
def test_dry_run_skip(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.skip
    def task_example_skip(): ...

    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Would be executed" in result.output
    assert "1  Skipped" in result.output
    assert not tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end
def test_dry_run_skip_all(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.skip
    @pytask.mark.produces("out.txt")
    def task_example_skip(): ...

    @pytask.mark.skip
    @pytask.mark.depends_on("out.txt")
    def task_example_skip_subsequent(): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Skipped" in result.output


@pytest.mark.end_to_end
def test_dry_run_skipped_successful(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Skipped because unchanged" in result.output


@pytest.mark.end_to_end
def test_dry_run_persisted(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.persist
    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output

    tmp_path.joinpath("out.txt").write_text("Changed text file.")

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Persisted" in result.output
