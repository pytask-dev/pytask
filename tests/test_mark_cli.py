from __future__ import annotations

import textwrap

import pytest
from pytask import cli
from pytask import main


@pytest.mark.end_to_end
def test_show_markers(runner):
    result = runner.invoke(cli, ["markers"])

    assert all(
        marker in result.output
        for marker in [
            "depends_on",
            "produces",
            "skip",
            "skip_ancestor_failed",
            "skip_unchanged",
        ]
    )


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_markers_option(tmp_path, runner, config_name):
    config_path = tmp_path.joinpath(config_name)
    config_path.write_text(
        textwrap.dedent(
            """
            [pytask]
            markers =
                a1: this is a webtest marker
                a1some: another marker
                nodescription
            """
        )
    )

    result = runner.invoke(cli, ["markers", "-c", config_path.as_posix()])

    assert all(marker in result.output for marker in ["a1", "a1some", "nodescription"])


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
@pytest.mark.parametrize("marker_name", ["lkasd alksds", "1kasd"])
def test_marker_names(tmp_path, marker_name, config_name):
    tmp_path.joinpath(config_name).write_text(
        textwrap.dedent(
            f"""
            [pytask]
            markers =
                {marker_name}
            """
        )
    )
    session = main({"paths": tmp_path, "markers": True})
    assert session.exit_code == 2
