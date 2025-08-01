from __future__ import annotations

import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest

from _pytask.skipping import pytask_execute_task_setup
from pytask import ExitCode
from pytask import Mark
from pytask import Session
from pytask import Skipped
from pytask import SkippedAncestorFailed
from pytask import SkippedUnchanged
from pytask import Task
from pytask import TaskOutcome
from pytask import build
from pytask import cli


class DummyClass:
    pass


def test_skip_unchanged(tmp_path):
    source = """
    def task_dummy():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS

    session = build(paths=tmp_path)
    assert isinstance(session.execution_reports[0].exc_info[1], SkippedUnchanged)


def test_skip_unchanged_w_dependencies_and_products(tmp_path):
    source = """
    from pathlib import Path

    def task_dummy(path=Path("in.txt"), produces=Path("out.txt")):
        produces.write_text(path.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Original content of in.txt.")

    session = build(paths=tmp_path)

    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS
    assert tmp_path.joinpath("out.txt").read_text() == "Original content of in.txt."

    session = build(paths=tmp_path)

    assert session.execution_reports[0].outcome == TaskOutcome.SKIP_UNCHANGED
    assert isinstance(session.execution_reports[0].exc_info[1], SkippedUnchanged)
    assert tmp_path.joinpath("out.txt").read_text() == "Original content of in.txt."


def test_skipif_ancestor_failed(tmp_path):
    source = """
    from pathlib import Path

    def task_first(produces=Path("out.txt")):
        assert 0

    def task_second(path=Path("out.txt")): ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.execution_reports[0].outcome == TaskOutcome.FAIL
    assert isinstance(session.execution_reports[0].exc_info[1], Exception)
    assert session.execution_reports[1].outcome == TaskOutcome.SKIP_PREVIOUS_FAILED
    assert isinstance(session.execution_reports[1].exc_info[1], SkippedAncestorFailed)


def test_if_skip_decorator_is_applied_to_following_tasks(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.skip
    def task_first(produces=Path("out.txt")):
        assert 0

    def task_second(path=Path("out.txt")): ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.execution_reports[0].outcome == TaskOutcome.SKIP
    assert isinstance(session.execution_reports[0].exc_info[1], Skipped)
    assert session.execution_reports[1].outcome == TaskOutcome.SKIP
    assert isinstance(session.execution_reports[1].exc_info[1], Skipped)


@pytest.mark.parametrize(
    "mark_string", ["@pytask.mark.skip", "@pytask.mark.skipif(True, reason='bla')"]
)
def test_skip_if_dependency_is_missing(tmp_path, mark_string):
    source = f"""
    import pytask
    from pathlib import Path

    {mark_string}
    def task_first(path=Path("in.txt")):
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.execution_reports[0].outcome == TaskOutcome.SKIP
    assert isinstance(session.execution_reports[0].exc_info[1], Skipped)


@pytest.mark.parametrize(
    "mark_string", ["@pytask.mark.skip", "@pytask.mark.skipif(True, reason='bla')"]
)
def test_skip_if_dependency_is_missing_only_for_one_task(runner, tmp_path, mark_string):
    source = f"""
    import pytask
    from pathlib import Path

    {mark_string}
    def task_first(path=Path("in.txt")):
        assert 0

    def task_second(path=Path("in.txt")):
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "in.txt" in result.output
    assert "task_first" not in result.output
    assert "task_second" in result.output


def test_if_skipif_decorator_is_applied_skipping(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.skipif(condition=True, reason="bla")
    def task_first(produces=Path("out.txt")):
        assert False

    def task_second(path=Path("out.txt")):
        assert False
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    node = session.collection_reports[0].node
    assert len(node.markers) == 1
    assert node.markers[0].name == "skipif"
    assert node.markers[0].args == ()
    assert node.markers[0].kwargs == {"condition": True, "reason": "bla"}

    assert session.execution_reports[0].outcome == TaskOutcome.SKIP
    assert isinstance(session.execution_reports[0].exc_info[1], Skipped)
    assert session.execution_reports[1].outcome == TaskOutcome.SKIP
    assert isinstance(session.execution_reports[1].exc_info[1], Skipped)
    assert session.execution_reports[0].exc_info[1].args[0] == "bla"


def test_if_skipif_decorator_is_applied_execute(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.skipif(False, reason="bla")
    def task_first(produces=Path("out.txt")):
        produces.touch()

    def task_second(path=Path("out.txt")): ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    node = session.collection_reports[0].node

    assert len(node.markers) == 1
    assert node.markers[0].name == "skipif"
    assert node.markers[0].args == (False,)
    assert node.markers[0].kwargs == {"reason": "bla"}
    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS
    assert session.execution_reports[0].exc_info is None
    assert session.execution_reports[1].outcome == TaskOutcome.SUCCESS
    assert session.execution_reports[1].exc_info is None


def test_if_skipif_decorator_is_applied_any_condition_matches(tmp_path):
    """Any condition of skipif has to be True and only their message is shown."""
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.skipif(condition=False, reason="I am fine")
    @pytask.mark.skipif(condition=True, reason="No, I am not.")
    def task_first(produces=Path("out.txt")):
        assert False

    def task_second(path=Path("out.txt")):
        assert False
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    node = session.collection_reports[0].node
    assert len(node.markers) == 2
    assert node.markers[0].name == "skipif"
    assert node.markers[0].args == ()
    assert node.markers[0].kwargs == {"condition": True, "reason": "No, I am not."}
    assert node.markers[1].name == "skipif"
    assert node.markers[1].args == ()
    assert node.markers[1].kwargs == {"condition": False, "reason": "I am fine"}

    assert session.execution_reports[0].outcome == TaskOutcome.SKIP
    assert isinstance(session.execution_reports[0].exc_info[1], Skipped)
    assert session.execution_reports[1].outcome == TaskOutcome.SKIP
    assert isinstance(session.execution_reports[1].exc_info[1], Skipped)
    assert session.execution_reports[0].exc_info[1].args[0] == "No, I am not."


@pytest.mark.parametrize(
    ("marker_name", "force", "expectation"),
    [
        ("skip_unchanged", False, pytest.raises(SkippedUnchanged)),
        ("skip_unchanged", True, does_not_raise()),
        ("skip_ancestor_failed", False, pytest.raises(SkippedAncestorFailed)),
        ("skip", False, pytest.raises(Skipped)),
        ("", False, does_not_raise()),
    ],
)
def test_pytask_execute_task_setup(marker_name, force, expectation):
    session = Session.from_config({"force": force})
    task = Task(base_name="task", path=Path(), function=None)
    kwargs = {"reason": ""} if marker_name == "skip_ancestor_failed" else {}
    task.markers = [Mark(marker_name, (), kwargs)]

    with expectation:
        pytask_execute_task_setup(session=session, task=task)


def test_skip_has_precedence_over_ancestor_failed(runner, tmp_path):
    source = """
    from pathlib import Path

    def task_example(produces=Path("file.txt")):
        raise Exception

    def task_example_2(path=Path("file.txt")): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
    assert "1  Failed" in result.output
    assert "1  Skipped" in result.output


def test_skipif_has_precedence_over_ancestor_failed(runner, tmp_path):
    source = """
    from pathlib import Path
    import pytask

    def task_example(produces=Path("file.txt")):
        raise Exception

    @pytask.mark.skipif(True, reason="God knows.")
    def task_example_2(path=Path("file.txt")): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
    assert "1  Failed" in result.output
    assert "1  Skipped" in result.output
