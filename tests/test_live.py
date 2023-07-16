from __future__ import annotations

import re
import textwrap

import pytest
from _pytask.live import LiveExecution
from _pytask.live import LiveManager
from _pytask.report import ExecutionReport
from pytask import cli
from pytask import ExitCode
from pytask import Task
from pytask import TaskOutcome


@pytest.mark.end_to_end()
@pytest.mark.parametrize("verbose", [0, 1])
def test_verbose_mode_execution(tmp_path, runner, verbose):
    source = "def task_example(): pass"
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--verbose", verbose])

    assert ("Task" in result.output) is (verbose >= 1)
    assert ("Outcome" in result.output) is (verbose >= 1)
    assert ("task_module.py::task_example" in result.output) is (verbose >= 1)


@pytest.mark.unit()
def test_live_execution_sequentially(capsys, tmp_path):
    path = tmp_path.joinpath("task_module.py")
    task = Task(base_name="task_example", path=path, function=lambda x: x)
    task.short_name = "task_module.py::task_example"

    live_manager = LiveManager()
    live = LiveExecution(
        live_manager=live_manager,
        n_entries_in_table=20,
        verbose=1,
        editor_url_scheme="no_link",
    )

    live_manager.start()
    live.update_running_tasks(task)
    live_manager.pause()

    # Test pause removes the table.
    captured = capsys.readouterr()
    assert "Task" not in captured.out
    assert "Outcome" not in captured.out
    assert "task_module.py::task_example" not in captured.out
    assert "running" not in captured.out
    assert "Completed: 0/x" not in captured.out

    live_manager.resume()
    live_manager.start()
    live_manager.stop()

    # Test table with running task.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_module.py::task_example" in captured.out
    assert "running" in captured.out
    assert "Completed: 0/x" in captured.out

    live_manager.start()

    report = ExecutionReport(task=task, outcome=TaskOutcome.SUCCESS, exc_info=None)

    live_manager.resume()
    live.update_reports(report)
    live_manager.stop()

    # Test final table with reported outcome.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_module.py::task_example" in captured.out
    assert "running" not in captured.out
    assert TaskOutcome.SUCCESS.symbol in captured.out
    assert "Completed: 1/x" in captured.out


@pytest.mark.unit()
@pytest.mark.parametrize("verbose", [1, 2])
@pytest.mark.parametrize("outcome", TaskOutcome)
def test_live_execution_displays_skips_and_persists(capsys, tmp_path, verbose, outcome):
    path = tmp_path.joinpath("task_module.py")
    task = Task(base_name="task_example", path=path, function=lambda x: x)
    task.short_name = "task_module.py::task_example"

    live_manager = LiveManager()
    live = LiveExecution(
        live_manager=live_manager,
        n_entries_in_table=20,
        verbose=verbose,
        editor_url_scheme="no_link",
    )

    live_manager.start()
    live.update_running_tasks(task)
    live_manager.pause()

    report = ExecutionReport(task=task, outcome=outcome, exc_info=None)

    live_manager.resume()
    live.update_reports(report)
    live_manager.stop()

    # Test final table with reported outcome.
    captured = capsys.readouterr()

    if verbose < 2 and outcome in (
        TaskOutcome.SKIP,
        TaskOutcome.SKIP_UNCHANGED,
        TaskOutcome.SKIP_PREVIOUS_FAILED,
        TaskOutcome.PERSISTENCE,
    ):
        # An empty table is not shown.
        assert "Task" not in captured.out
        assert "Outcome" not in captured.out

        assert "task_module.py::task_example" not in captured.out
        assert f"│ {outcome.symbol}" not in captured.out
    else:
        assert "Task" in captured.out
        assert "Outcome" in captured.out
        assert "task_module.py::task_example" in captured.out
        assert f"│ {outcome.symbol}" in captured.out

    assert "running" not in captured.out


@pytest.mark.unit()
@pytest.mark.parametrize("n_entries_in_table", [1, 2])
def test_live_execution_displays_subset_of_table(capsys, tmp_path, n_entries_in_table):
    path = tmp_path.joinpath("task_module.py")
    running_task = Task(base_name="task_running", path=path, function=lambda x: x)
    running_task.short_name = "task_module.py::task_running"

    live_manager = LiveManager()
    live = LiveExecution(
        live_manager=live_manager,
        n_entries_in_table=n_entries_in_table,
        verbose=1,
        editor_url_scheme="no_link",
        n_tasks=2,
    )

    live_manager.start()
    live.update_running_tasks(running_task)
    live_manager.stop(transient=False)

    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "::task_running" in captured.out
    assert " running " in captured.out
    assert "Completed: 0/2" in captured.out

    completed_task = Task(base_name="task_completed", path=path, function=lambda x: x)
    completed_task.short_name = "task_module.py::task_completed"
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
    assert "Completed: 1/2" in captured.out

    if n_entries_in_table == 1:
        assert "task_module.py::task_completed" not in captured.out
        assert "│ ." not in captured.out
    else:
        assert "task_module.py::task_completed" in captured.out
        assert "│ ." in captured.out


@pytest.mark.unit()
@pytest.mark.xfail(reason="See #377.")
def test_live_execution_skips_do_not_crowd_out_displayed_tasks(capsys, tmp_path):
    path = tmp_path.joinpath("task_module.py")
    task = Task(base_name="task_example", path=path, function=lambda x: x)
    task.short_name = "task_module.py::task_example"

    live_manager = LiveManager()
    live = LiveExecution(
        live_manager=live_manager,
        n_entries_in_table=20,
        verbose=1,
        editor_url_scheme="no_link",
    )

    live_manager.start()
    live.update_running_tasks(task)
    live_manager.stop()

    # Test table with running task.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_module.py::task_example" in captured.out
    assert "running" in captured.out

    # Add one displayed reports and many more not displayed reports to crowd out the
    # valid one.
    successful_task = Task(base_name="task_success", path=path, function=lambda x: x)
    successful_task.short_name = "task_module.py::task_success"

    tasks = []
    for i in range(25):
        skipped_task = Task(base_name=f"task_skip_{i}", path=path, function=lambda x: x)
        skipped_task.short_name = f"task_module.py::task_skip_{i}"
        tasks.append(skipped_task)

    live_manager.start()
    live.update_running_tasks(successful_task)
    for task in tasks:
        live.update_running_tasks(task)
    live_manager.stop()

    captured = capsys.readouterr()
    assert "running" in captured.out
    assert "task_success" in captured.out
    for i in range(25):
        assert f"task_skip_{i}" in captured.out

    live_manager.resume()
    report = ExecutionReport(
        task=successful_task, outcome=TaskOutcome.SUCCESS, exc_info=None
    )
    live.update_reports(report)
    for task in tasks:
        report = ExecutionReport(task=task, outcome=TaskOutcome.SKIP, exc_info=None)
        live.update_reports(report)
    live_manager.stop()

    # Test final table with reported outcome.
    captured = capsys.readouterr()
    assert "Task" in captured.out
    assert "Outcome" in captured.out
    assert "task_module.py::task_example" in captured.out
    assert "task_module.py::task_success" in captured.out
    assert "running" in captured.out
    assert TaskOutcome.SUCCESS.symbol in captured.out
    assert "task_skip" not in captured.out


@pytest.mark.end_to_end()
def test_full_execution_table_is_displayed_at_the_end_of_execution(tmp_path, runner):
    source = """
    import pytask

    for produces in [f"{i}.txt" for i in range(4)]:

        @pytask.mark.task
        def task_create_file(produces=produces):
            produces.touch()
    """
    # Subfolder to reduce task id and be able to check the output later.
    tmp_path.joinpath("d").mkdir()
    tmp_path.joinpath("d", "task_t.py").write_text(textwrap.dedent(source))

    result = runner.invoke(
        cli, [tmp_path.joinpath("d").as_posix(), "--n-entries-in-table=1"]
    )

    assert result.exit_code == ExitCode.OK
    for i in range(4):
        assert f"{i}.txt" in result.output


@pytest.mark.end_to_end()
@pytest.mark.parametrize("sort_table", ["true", "false"])
def test_sort_table_option(tmp_path, runner, sort_table):
    source = """
    import pytask

    def task_a():
        pass

    @pytask.mark.try_first
    def task_b():
        pass

    """
    tmp_path.joinpath("task_order.py").write_text(textwrap.dedent(source))

    config = f"[tool.pytask.ini_options]\nsort_table = {sort_table}"
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(config))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    lines = result.output.split("\n")
    task_names = [re.findall("task_[a|b]", line) for line in lines]
    task_names = [name[0][-1] for name in task_names if name]
    expected = ["a", "b"] if sort_table == "true" else ["b", "a"]
    assert expected == task_names


@pytest.mark.end_to_end()
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

    assert result.exit_code == ExitCode.OK
    assert "task_func" in result.output
