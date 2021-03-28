import attr
import pytest
from _pytask.logging import _format_plugin_names_and_versions
from _pytask.logging import pytask_log_session_footer


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
            [(1, "succeeded", "green"), (1, "failed", "red")],
            1,
            "red",
            "────── 1 succeeded, 1 failed in 1s ───────────",
        ),
        (
            [(2, "succeeded", "green"), (1, "skipped", "yellow")],
            10,
            "green",
            "────── 2 succeeded, 1 skipped in 10s ───────────",
        ),
    ],
)
def test_pytask_log_session_footer(capsys, infos, duration, color, expected):
    pytask_log_session_footer(infos, duration, color)
    captured = capsys.readouterr()
    assert expected in captured.out
