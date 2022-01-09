import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import attr
import pytest
from _pytask.enums import ExitCode
from _pytask.logging import _format_plugin_names_and_versions
from _pytask.logging import _humanize_time
from _pytask.logging import pytask_log_session_footer
from _pytask.outcomes import TaskOutcome
from pytask import cli


@attr.s
class DummyDist:
    project_name = attr.ib()
    version = attr.ib()


@pytest.mark.unit
@pytest.mark.parametrize(
    "plugins, expected",
    [
        ([(None, DummyDist("pytask-plugin", "0.0.1"))], ["plugin-0.0.1"]),
        ([(None, DummyDist("plugin", "1.0.0"))], ["plugin-1.0.0"]),
    ],
)
def test_format_plugin_names_and_versions(plugins, expected):
    assert _format_plugin_names_and_versions(plugins) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "duration, outcome, expected",
    [
        (
            1,
            TaskOutcome.FAIL,
            "────── Failed in 1 second ───────────",
        ),
        (
            10,
            TaskOutcome.SUCCESS,
            "────── Succeeded in 10 seconds ─────",
        ),
        (
            5401,
            TaskOutcome.SUCCESS,
            "─ Succeeded in 1 hour, 30 minutes ─",
        ),
        (
            125_000,
            TaskOutcome.FAIL,
            "─────── Failed in 1 day, 10 hours, 43 minutes ───────────",
        ),
    ],
)
def test_pytask_log_session_footer(capsys, duration, outcome, expected):
    pytask_log_session_footer(duration, outcome)
    captured = capsys.readouterr()
    assert expected in captured.out


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "func, expected_1, expected_2",
    [
        ("def task_func(): pass", "1  Succeeded", "1  Skipped because unchanged"),
        (
            "@pytask.mark.persist\n    def task_func(): pass",
            "1  Persisted",
            "1  Skipped because unchanged",
        ),
        ("@pytask.mark.skip\n    def task_func(): pass", "1  Skipped", "1  Skipped"),
        (
            "@pytask.mark.skip_unchanged\n    def task_func(): pass",
            "1  Skipped because unchanged",
            "1  Skipped because unchanged",
        ),
        (
            "@pytask.mark.skip_ancestor_failed\n    def task_func(): pass",
            "1  Skipped because previous failed",
            "1  Skipped because previous failed",
        ),
        ("def task_func(): raise Exception", "1  Failed", "1  Failed"),
    ],
)
def test_logging_of_outcomes(tmp_path, runner, func, expected_1, expected_2):
    source = f"""
    import pytask

    {func}
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert expected_1 in result.output

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert expected_2 in result.output


@pytest.mark.unit
@pytest.mark.parametrize(
    "amount, unit, short_label, expectation, expected",
    [
        (2.234, "seconds", True, does_not_raise(), [(2.23, "s")]),
        (173, "hours", True, does_not_raise(), [(7, "d"), (5, "h")]),
        (1, "hour", False, does_not_raise(), [(1, "hour")]),
        (
            17281,
            "seconds",
            False,
            does_not_raise(),
            [(4, "hours"), (48, "minutes"), (1, "second")],
        ),
        (1, "hour", True, does_not_raise(), [(1, "h")]),
        (
            1,
            "unknown_unit",
            False,
            pytest.raises(ValueError, match="The time unit"),
            None,
        ),
    ],
)
def test_humanize_time(amount, unit, short_label, expectation, expected):
    with expectation:
        result = _humanize_time(amount, unit, short_label)
        assert result == expected


@pytest.mark.parametrize("show_traceback", ["no", "yes"])
def test_show_traceback(runner, tmp_path, show_traceback):
    source = "def task_raises(): raise Exception"
    tmp_path.joinpath("task_module.py").write_text(source)

    result = runner.invoke(
        cli, [tmp_path.as_posix(), "--show-traceback", show_traceback]
    )

    has_traceback = show_traceback == "yes"

    assert result.exit_code == ExitCode.FAILED
    assert ("Failures" in result.output) is has_traceback
    assert ("Traceback" in result.output) is has_traceback
    assert ("raise Exception" in result.output) is has_traceback
