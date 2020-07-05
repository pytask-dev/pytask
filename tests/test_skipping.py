import os
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from pytask.main import main
from pytask.mark import Mark
from pytask.outcomes import Skipped
from pytask.outcomes import SkippedAncestorFailed
from pytask.outcomes import SkippedUnchanged
from pytask.report import ExecutionReport
from pytask.skipping import pytask_execute_task_log_end
from pytask.skipping import pytask_execute_task_setup


@pytest.mark.end_to_end
def test_skip_unchanged(tmp_path):
    source = """
    def task_dummy():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})
    assert session.execution_reports[0].success

    session = main({"paths": tmp_path})
    assert isinstance(session.execution_reports[0].exc_info[1], SkippedUnchanged)


@pytest.mark.end_to_end
def test_skip_unchanged_w_dependencies_and_products(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy():
        in_ = Path("in.txt").read_text()
        Path("out.txt").write_text(in_)
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Original content of in.txt.")

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert session.execution_reports[0].success
    assert tmp_path.joinpath("out.txt").read_text() == "Original content of in.txt."

    session = main({"paths": tmp_path})

    assert isinstance(session.execution_reports[0].exc_info[1], SkippedUnchanged)
    assert tmp_path.joinpath("out.txt").read_text() == "Original content of in.txt."


@pytest.mark.end_to_end
def test_skip_if_ancestor_failed(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.produces("out.txt")
    def task_first():
        assert 0


    @pytask.mark.depends_on("out.txt")
    def task_second():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert not session.execution_reports[0].success
    assert isinstance(session.execution_reports[0].exc_info[1], Exception)
    assert not session.execution_reports[1].success
    assert isinstance(session.execution_reports[1].exc_info[1], SkippedAncestorFailed)


def test_if_skip_decorator_is_applied(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.skip
    @pytask.mark.produces("out.txt")
    def task_first():
        assert 0


    @pytask.mark.depends_on("out.txt")
    def task_second():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert session.execution_reports[0].success
    assert isinstance(session.execution_reports[0].exc_info[1], Skipped)
    assert session.execution_reports[1].success
    assert isinstance(session.execution_reports[1].exc_info[1], Skipped)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("marker_name", "expectation"),
    [
        ("skip_unchanged", pytest.raises(SkippedUnchanged)),
        ("skip_ancestor_failed", pytest.raises(SkippedAncestorFailed)),
        ("skip", pytest.raises(Skipped)),
        ("", does_not_raise()),
    ],
)
def test_pytask_execute_task_setup(marker_name, expectation):
    class Task:
        pass

    task = Task()
    kwargs = {"reason": ""} if marker_name == "skip_ancestor_failed" else {}
    task.markers = [Mark(marker_name, (), kwargs)]

    with expectation:
        pytask_execute_task_setup(task)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exception", "character"),
    [
        (SkippedUnchanged, "s"),
        (SkippedAncestorFailed, "s"),
        (Skipped, "s"),
        (None, ""),
    ],
)
def test_pytask_execute_task_log_end(capsys, exception, character):
    if isinstance(exception, (Skipped, SkippedUnchanged)):
        report = ExecutionReport.from_task_and_exception((), exception())
        report.success = True
    elif isinstance(exception, SkippedAncestorFailed):
        report = ExecutionReport.from_task_and_exception((), SkippedAncestorFailed)
        report.success = True
    else:
        report = ExecutionReport.from_task(())

    out = pytask_execute_task_log_end(report)

    captured = capsys.readouterr()
    if isinstance(exception, (Skipped, SkippedUnchanged)):
        assert out
        assert captured.out == character
    else:
        assert out is None
        assert captured.out == ""
