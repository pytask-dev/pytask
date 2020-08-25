import attr
import pytest
from _pytask.logging import _format_plugin_names_and_versions


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
