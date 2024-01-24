from __future__ import annotations

import textwrap

import pytest
from pytask import cli
from pytask import ExitCode


@pytest.mark.end_to_end()
def test_dry_run(runner, tmp_path):
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")): produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Would be executed" in result.output
    assert not tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end()
def test_dry_run_w_subsequent_task(runner, tmp_path):
    """Subsequent tasks would be executed if their previous task changed."""
    source = """
    from pathlib import Path

    def task_example(path=Path("out.txt"), produces=Path("out_2.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example_second.py").write_text(textwrap.dedent(source))

    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example_first.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output

    # Add a new line to the file or the task would be skipped.
    tmp_path.joinpath("task_example_first.py").write_text(
        textwrap.dedent(source + "\n")
    )

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Would be executed" in result.output


@pytest.mark.end_to_end()
def test_dry_run_w_subsequent_skipped_task(runner, tmp_path):
    """A skip is more important than a would be run."""
    source_1 = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example_first.py").write_text(textwrap.dedent(source_1))

    source_2 = """
    from pathlib import Path

    def task_example(path=Path("out.txt"), produces=Path("out_2.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example_second.py").write_text(textwrap.dedent(source_2))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output

    tmp_path.joinpath("task_example_first.py").write_text(textwrap.dedent(source_1))
    tmp_path.joinpath("task_example_second.py").write_text(
        textwrap.dedent(source_2 + "\n")
    )

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Would be executed" in result.output
    assert "1  Skipped" in result.output


@pytest.mark.end_to_end()
def test_dry_run_skip(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.skip
    def task_example_skip(): ...

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Would be executed" in result.output
    assert "1  Skipped" in result.output
    assert not tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end()
def test_dry_run_skip_all(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.skip
    def task_example_skip(produces=Path("out.txt")): ...

    @pytask.mark.skip
    def task_example_skip_subsequent(path=Path("out.txt")): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Skipped" in result.output


@pytest.mark.end_to_end()
def test_dry_run_skipped_successful(runner, tmp_path):
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output

    result = runner.invoke(cli, ["--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Skipped because unchanged" in result.output


@pytest.mark.end_to_end()
def test_dry_run_persisted(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.persist
    def task_example(produces=Path("out.txt")):
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
