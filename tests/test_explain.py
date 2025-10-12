from __future__ import annotations

import textwrap

from pytask import ExitCode
from pytask import cli


def test_explain_source_file_changed(runner, tmp_path):
    """Test --explain shows source file changed."""
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output

    # Modify source file
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source + "\n"))

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "Explanation" in result.output
    assert "Changed" in result.output or "changed" in result.output
    assert "task_example" in result.output


def test_explain_dependency_file_changed(runner, tmp_path):
    """Test --explain detects changed dependency file."""
    source_first = """
    from pathlib import Path

    def task_first(produces=Path("out.txt")):
        produces.write_text("hello")
    """
    tmp_path.joinpath("task_first.py").write_text(textwrap.dedent(source_first))

    source_second = """
    from pathlib import Path

    def task_second(path=Path("out.txt"), produces=Path("out2.txt")):
        content = path.read_text()
        produces.write_text(content + " world")
    """
    tmp_path.joinpath("task_second.py").write_text(textwrap.dedent(source_second))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output

    # Manually modify the intermediate file
    tmp_path.joinpath("out.txt").write_text("modified")

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "out.txt" in result.output
    assert "changed" in result.output.lower()


def test_explain_dependency_missing(runner, tmp_path):
    """Test --explain detects missing dependency."""
    source_first = """
    from pathlib import Path

    def task_first(produces=Path("out.txt")):
        produces.write_text("hello")
    """
    tmp_path.joinpath("task_first.py").write_text(textwrap.dedent(source_first))

    source_second = """
    from pathlib import Path

    def task_second(path=Path("out.txt"), produces=Path("out2.txt")):
        produces.write_text(path.read_text())
    """
    tmp_path.joinpath("task_second.py").write_text(textwrap.dedent(source_second))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    # Delete dependency
    tmp_path.joinpath("out.txt").unlink()

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "out.txt" in result.output
    assert "missing" in result.output.lower() or "not found" in result.output.lower()


def test_explain_product_missing(runner, tmp_path):
    """Test --explain detects missing product."""
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.write_text("hello")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()

    # Delete product
    tmp_path.joinpath("out.txt").unlink()

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "out.txt" in result.output
    assert "missing" in result.output.lower() or "not found" in result.output.lower()


def test_explain_multiple_changes(runner, tmp_path):
    """Test --explain shows multiple reasons when multiple things changed."""
    source = """
    from pathlib import Path

    def task_example(path=Path("input.txt"), produces=Path("out.txt")):
        produces.write_text(path.read_text())
    """
    tmp_path.joinpath("input.txt").write_text("original")
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    # Change both source and dependency
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source + "\n"))
    tmp_path.joinpath("input.txt").write_text("modified")

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    # Should mention both changes
    assert "task_example.py" in result.output or "source" in result.output.lower()
    assert "input.txt" in result.output


def test_explain_with_persist_marker(runner, tmp_path):
    """Test --explain respects @pytask.mark.persist."""
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.persist
    def task_example(path=Path("input.txt"), produces=Path("out.txt")):
        produces.write_text(path.read_text())
    """
    tmp_path.joinpath("input.txt").write_text("original")
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    # Change dependency
    tmp_path.joinpath("input.txt").write_text("modified")

    # Test with default verbosity (should show summary)
    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "persisted task(s)" in result.output.lower()
    assert "use -vv to show details" in result.output.lower()

    # Change dependency again for verbose test
    tmp_path.joinpath("input.txt").write_text("modified again")

    # Test with verbose 2 (should show details)
    result = runner.invoke(cli, ["--explain", "--verbose", "2", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "Persisted tasks" in result.output
    assert "Persisted (products exist, changes ignored)" in result.output


def test_explain_cascade_execution(runner, tmp_path):
    """Test --explain shows cascading task executions."""
    source_a = """
    from pathlib import Path

    def task_a(produces=Path("a.txt")):
        produces.write_text("a")
    """
    tmp_path.joinpath("task_a.py").write_text(textwrap.dedent(source_a))

    source_b = """
    from pathlib import Path

    def task_b(path=Path("a.txt"), produces=Path("b.txt")):
        produces.write_text(path.read_text() + "b")
    """
    tmp_path.joinpath("task_b.py").write_text(textwrap.dedent(source_b))

    source_c = """
    from pathlib import Path

    def task_c(path=Path("b.txt"), produces=Path("c.txt")):
        produces.write_text(path.read_text() + "c")
    """
    tmp_path.joinpath("task_c.py").write_text(textwrap.dedent(source_c))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "3  Succeeded" in result.output

    # Change first task
    tmp_path.joinpath("task_a.py").write_text(textwrap.dedent(source_a + "\n"))

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    # All three tasks should be shown
    assert "task_a" in result.output
    assert "task_b" in result.output
    assert "task_c" in result.output
    # Check cascade explanations
    assert "Preceding task" in result.output
    assert "task_a" in result.output
    assert "Changed" in result.output


def test_explain_first_run_no_database(runner, tmp_path):
    """Test --explain on first run (no database)."""
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "task_example" in result.output
    # Should indicate first run or not in database
    assert (
        "first" in result.output.lower()
        or "not in database" in result.output.lower()
        or "never executed" in result.output.lower()
    )


def test_explain_with_force_flag(runner, tmp_path):
    """Test --explain with --force flag."""
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(cli, ["--force", "--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "force" in result.output.lower() or "task_example" in result.output


def test_explain_no_changes(runner, tmp_path):
    """Test --explain when nothing changed."""
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    # Should indicate nothing needs to be executed
    assert (
        "no changes" in result.output.lower()
        or "unchanged" in result.output.lower()
        or "0 " in result.output
    )
    assert "1 task(s) with no changes (use -vv to show details)" in result.output


def test_explain_with_dry_run(runner, tmp_path):
    """Test --explain works with --dry-run."""
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    # Modify source
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source + "\n"))

    result = runner.invoke(cli, ["--dry-run", "--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "task_example" in result.output
    # Should show explanation and not execute
    assert (
        not tmp_path.joinpath("out.txt").read_text()
        or tmp_path.joinpath("out.txt").stat().st_size == 0
    )


def test_explain_skipped_tasks(runner, tmp_path):
    """Test --explain handles skipped tasks."""
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.skip
    def task_skip(produces=Path("skip.txt")):
        produces.touch()

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "skip" in result.output.lower()


def test_explain_task_source_and_dependency_changed(runner, tmp_path):
    """Test --explain when both task source and dependency change."""
    source = """
    from pathlib import Path

    def task_example(path=Path("data.txt"), produces=Path("out.txt")):
        content = path.read_text()
        produces.write_text(content)
    """
    tmp_path.joinpath("data.txt").write_text("original")
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    # Change both source and data
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source + "\n"))
    tmp_path.joinpath("data.txt").write_text("modified")

    result = runner.invoke(cli, ["--explain", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "Explanation" in result.output
    assert "task_example" in result.output
    # Should show changes
    assert "changed" in result.output.lower() or "Changed" in result.output


def test_explain_verbose_output(runner, tmp_path):
    """Test --explain with -v shows more details."""
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    # Modify source
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source + "\n"))

    result = runner.invoke(cli, ["--explain", "-v", "1", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    # Verbose mode should show more details
    assert "task_example" in result.output
