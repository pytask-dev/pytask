from __future__ import annotations

import shutil
from pathlib import Path

from pytask import ExitCode
from pytask import cli


def test_completed_portability_fixture_is_skipped(runner, tmp_path):
    fixture = (
        Path(__file__).resolve().parent
        / "_test_data"
        / "portability_projects"
        / "basic_completed"
    )
    project = tmp_path / "basic_completed"
    shutil.copytree(fixture, project)

    original_lockfile = project.joinpath("pytask.lock").read_text()

    result = runner.invoke(cli, [project.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Skipped because unchanged" in result.output
    assert "1  Succeeded" not in result.output
    assert project.joinpath("pytask.lock").read_text() == original_lockfile
