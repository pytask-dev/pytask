import textwrap

import pytest
from _pytask.live import LiveExecution
from _pytask.nodes import PythonFunctionTask
from _pytask.report import ExecutionReport
from pytask import cli


@pytest.mark.end_to_end
@pytest.mark.parametrize("verbose", [False, True])
def test_verbose_mode_execution(tmp_path, runner, verbose):
    source = "def task_dummy(): pass"
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    args = [tmp_path.as_posix()]
    if verbose:
        args.append("-v")
    result = runner.invoke(cli, args)

    assert ("Task" in result.output) is verbose
    assert ("Outcome" in result.output) is verbose
    assert ("└──" in result.output) is verbose
    assert ("task_dummy.py::task_dummy" in result.output) is verbose


@pytest.mark.unit
def test_live_execution_sequentially(capsys, tmp_path):
    path = tmp_path.joinpath("task_dummy.py")
    task = PythonFunctionTask(
        "task_dummy", path.as_posix() + "::task_dummy", path, None
    )

    live = LiveExecution(True, [tmp_path])

    live.start()
    live.update_running_tasks(task)
    live.pause()

    captured = capsys.readouterr()
    assert "Task" not in captured.out
    assert "Outcome" not in captured.out
    assert "task_dummy.py::task_dummy" not in captured.out
    assert "running" not in captured.out

    live.resume()
    live.start()
    live.stop()

    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_dummy.py::task_dummy" in captured.out
    assert "running" in captured.out

    live.start()

    report = ExecutionReport(
        task=task, success=True, exc_info=None, symbol="new_symbol", color="black"
    )

    live.resume()
    live.update_reports(report)
    live.stop()

    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_dummy.py::task_dummy" in captured.out
    assert "running" not in captured.out
    assert "new_symbol" in captured.out
