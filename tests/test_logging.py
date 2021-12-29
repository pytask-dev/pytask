import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import attr
import pytest
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
    "infos, duration, color, expected",
    [
        (
            {TaskOutcome.SUCCESS: 1, TaskOutcome.FAIL: 1},
            1,
            TaskOutcome.FAIL.style,
            "────── 1 succeeded, 1 failed in 1 second ───────────",
        ),
        (
            {TaskOutcome.SUCCESS: 1, TaskOutcome.SKIP_PREVIOUS_FAILED: 1},
            10,
            TaskOutcome.SUCCESS.style,
            "────── 1 succeeded, 1 skipped because previous failed in 10 seconds ─────",
        ),
        (
            {TaskOutcome.SKIP_UNCHANGED: 1, TaskOutcome.PERSISTENCE: 1},
            5401,
            TaskOutcome.SUCCESS.style,
            "─ 1 skipped because unchanged, 1 persisted in 1 hour, 30 minutes ─",
        ),
        (
            {TaskOutcome.FAIL: 1, TaskOutcome.SKIP: 1},
            125_000,
            TaskOutcome.FAIL.style,
            "─────── 1 failed, 1 skipped in 1 day, 10 hours, 43 minutes ───────────",
        ),
    ],
)
def test_pytask_log_session_footer(capsys, infos, duration, color, expected):
    pytask_log_session_footer(infos, duration, color)
    captured = capsys.readouterr()
    assert expected in captured.out


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "func, expected_1, expected_2",
    [
        ("def task_func(): pass", "1 succeeded", "1 skipped because unchanged"),
        (
            "@pytask.mark.persist\n    def task_func(): pass",
            "1 persisted",
            "1 skipped because unchanged",
        ),
        ("@pytask.mark.skip\n    def task_func(): pass", "1 skipped", "1 skipped"),
        (
            "@pytask.mark.skip_unchanged\n    def task_func(): pass",
            "1 skipped because unchanged",
            "1 skipped because unchanged",
        ),
        (
            "@pytask.mark.skip_ancestor_failed\n    def task_func(): pass",
            "1 skipped because previous failed",
            "1 skipped because previous failed",
        ),
        ("def task_func(): raise Exception", "1 failed", "1 failed"),
    ],
)
def test_logging_of_outcomes(tmp_path, runner, func, expected_1, expected_2):
    source = f"""
    import pytask

    {func}
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert expected_1 in result.output

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert expected_2 in result.output


@pytest.mark.unit
@pytest.mark.parametrize(
    "amount, unit, short_label, expectation, expected",
    [
        (173, "hours", False, does_not_raise(), [(7, "days"), (5, "hours")]),
        (1, "hour", False, does_not_raise(), [(1, "hour")]),
        (
            17281,
            "seconds",
            False,
            does_not_raise(),
            [(4, "hours"), (48, "minutes"), (1, "second")],
        ),
        (173, "hours", True, does_not_raise(), [(7, "d"), (5, "h")]),
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
