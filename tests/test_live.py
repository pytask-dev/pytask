import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytest
from _pytask.live import _parse_n_entries_in_table
from _pytask.live import LiveExecution
from _pytask.live import LiveManager
from _pytask.nodes import PythonFunctionTask
from _pytask.outcomes import TaskOutcome
from _pytask.report import ExecutionReport
from pytask import cli


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expectation, expected",
    [
        pytest.param(None, does_not_raise(), None, id="none parsed"),
        pytest.param(3, does_not_raise(), 3, id="int parsed"),
        pytest.param("10", does_not_raise(), 10, id="string int parsed"),
        pytest.param("all", does_not_raise(), 1_000_000, id="all to large int"),
        pytest.param(
            -1,
            pytest.raises(ValueError, match="'n_entries_in_table' can"),
            None,
            id="negative int raises error",
        ),
        pytest.param(
            "-1",
            pytest.raises(ValueError, match="'n_entries_in_table' can"),
            None,
            id="negative int raises error",
        ),
    ],
)
def test_parse_n_entries_in_table(value, expectation, expected):
    with expectation:
        result = _parse_n_entries_in_table(value)
        assert result == expected


@pytest.mark.end_to_end
@pytest.mark.parametrize("verbose", [False, True])
def test_verbose_mode_execution(tmp_path, runner, verbose):
    source = "def task_dummy(): pass"
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    args = [tmp_path.as_posix()]
    if not verbose:
        args.append("-v 0")
    result = runner.invoke(cli, args)

    assert ("Task" in result.output) is verbose
    assert ("Outcome" in result.output) is verbose
    assert ("task_dummy.py::task_dummy" in result.output) is verbose


@pytest.mark.unit
def test_live_execution_sequentially(capsys, tmp_path):
    path = tmp_path.joinpath("task_dummy.py")
    task = PythonFunctionTask(
        "task_dummy", path.as_posix() + "::task_dummy", path, lambda x: x
    )

    live_manager = LiveManager()
    live = LiveExecution(live_manager, [tmp_path], 20, 1)

    live_manager.start()
    live.update_running_tasks(task)
    live_manager.pause()

    # Test pause removes the table.
    captured = capsys.readouterr()
    assert "Task" not in captured.out
    assert "Outcome" not in captured.out
    assert "task_dummy.py::task_dummy" not in captured.out
    assert "running" not in captured.out

    live_manager.resume()
    live_manager.start()
    live_manager.stop()

    # Test table with running task.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_dummy.py::task_dummy" in captured.out
    assert "running" in captured.out

    live_manager.start()

    report = ExecutionReport(task=task, outcome=TaskOutcome.SUCCESS, exc_info=None)

    live_manager.resume()
    live.update_reports(report)
    live_manager.stop()

    # Test final table with reported outcome.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_dummy.py::task_dummy" in captured.out
    assert "running" not in captured.out
    assert TaskOutcome.SUCCESS.symbol in captured.out


@pytest.mark.unit
@pytest.mark.parametrize("verbose", [1, 2])
@pytest.mark.parametrize("outcome", TaskOutcome)
def test_live_execution_displays_skips_and_persists(capsys, tmp_path, verbose, outcome):
    path = tmp_path.joinpath("task_dummy.py")
    task = PythonFunctionTask(
        "task_dummy", path.as_posix() + "::task_dummy", path, lambda x: x
    )

    live_manager = LiveManager()
    live = LiveExecution(live_manager, [tmp_path], 20, verbose)

    live_manager.start()
    live.update_running_tasks(task)
    live_manager.pause()

    report = ExecutionReport(task=task, outcome=outcome, exc_info=None)

    live_manager.resume()
    live.update_reports(report)
    live_manager.stop()

    # Test final table with reported outcome.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out

    if verbose < 2 and outcome in (
        TaskOutcome.SKIP,
        TaskOutcome.SKIP_UNCHANGED,
        TaskOutcome.SKIP_PREVIOUS_FAILED,
        TaskOutcome.PERSISTENCE,
    ):
        assert "task_dummy.py::task_dummy" not in captured.out
        assert f"│ {outcome.symbol}" not in captured.out
    else:
        assert "task_dummy.py::task_dummy" in captured.out
        assert f"│ {outcome.symbol}" in captured.out

    assert "running" not in captured.out


@pytest.mark.unit
@pytest.mark.parametrize("n_entries_in_table", [1, 2])
def test_live_execution_displays_subset_of_table(capsys, tmp_path, n_entries_in_table):
    path = tmp_path.joinpath("task_dummy.py")
    running_task = PythonFunctionTask(
        "task_running", path.as_posix() + "::task_running", path, lambda x: x
    )

    live_manager = LiveManager()
    live = LiveExecution(live_manager, [tmp_path], n_entries_in_table, 1)

    live_manager.start()
    live.update_running_tasks(running_task)
    live_manager.stop()

    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "::task_running" in captured.out
    assert " running " in captured.out

    completed_task = PythonFunctionTask(
        "task_completed", path.as_posix() + "::task_completed", path, lambda x: x
    )
    live.update_running_tasks(completed_task)
    report = ExecutionReport(
        task=completed_task, outcome=TaskOutcome.SUCCESS, exc_info=None
    )

    live_manager.resume()
    live.update_reports(report)
    live_manager.stop()

    # Test that report is or is not included.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "::task_running" in captured.out
    assert " running " in captured.out

    if n_entries_in_table == 1:
        assert "task_dummy.py::task_completed" not in captured.out
        assert "│ ." not in captured.out
    else:
        assert "task_dummy.py::task_completed" in captured.out
        assert "│ ." in captured.out


@pytest.mark.end_to_end
def test_full_execution_table_is_displayed_at_the_end_of_execution(tmp_path, runner):
    source = """
    import pytask

    @pytask.mark.parametrize("produces", [f"{i}.txt" for i in range(4)])
    def task_create_file(produces):
        produces.touch()
    """
    # Subfolder to reduce task id and be able to check the output later.
    tmp_path.joinpath("d").mkdir()
    tmp_path.joinpath("d", "task_t.py").write_text(textwrap.dedent(source))

    result = runner.invoke(
        cli, [tmp_path.joinpath("d").as_posix(), "--n-entries-in-table=1"]
    )

    assert result.exit_code == 0
    for i in range(4):
        assert f"{i}.txt" in result.output


@pytest.mark.end_to_end
def test_execute_w_partialed_functions(tmp_path, runner):
    """Test with partialed function which make it harder to extract info.

    Info like source line number and the path to the module.

    """
    source = """
    import functools

    def func(): ...

    task_func = functools.partial(func)

    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.joinpath("task_module.py").as_posix()])

    assert result.exit_code == 0
    assert "task_func" in result.output
