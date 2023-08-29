from __future__ import annotations

import textwrap

import pytest
from pytask import build
from pytask import cli
from pytask import ExitCode


@pytest.mark.end_to_end()
def test_show_markers(runner):
    result = runner.invoke(cli, ["markers"])

    assert all(
        marker in result.output
        for marker in (
            "depends_on",
            "produces",
            "skip",
            "skip_ancestor_failed",
            "skip_unchanged",
        )
    )


@pytest.mark.end_to_end()
def test_markers_option(tmp_path, runner):
    toml = """
    [tool.pytask.ini_options.markers]
    a1 = "this is a webtest marker"
    a1some = "another marker"
    nodescription = ""
    """
    config_path = tmp_path.joinpath("pyproject.toml")
    config_path.write_text(textwrap.dedent(toml))

    result = runner.invoke(cli, ["markers", "-c", config_path.as_posix()])

    assert all(marker in result.output for marker in ("a1", "a1some", "nodescription"))


@pytest.mark.end_to_end()
@pytest.mark.parametrize("marker_name", ["lkasd alksds", "1kasd"])
def test_marker_names(tmp_path, marker_name):
    toml = f"""
    [tool.pytask.ini_options.markers]
    markers = ['{marker_name}']
    """
    tmp_path.joinpath("pyproject.toml").write_text(textwrap.dedent(toml))
    session = build({"paths": tmp_path, "markers": True})
    assert session.exit_code == ExitCode.CONFIGURATION_FAILED
