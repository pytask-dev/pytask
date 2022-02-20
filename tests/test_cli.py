from __future__ import annotations

import subprocess

import pytest
from _pytask.outcomes import ExitCode
from pytask import __version__
from pytask import cli


@pytest.mark.end_to_end
def test_version_option():
    process = subprocess.run(["pytask", "--version"], capture_output=True)
    assert "pytask, version " + __version__ in process.stdout.decode("utf-8")


@pytest.mark.end_to_end
@pytest.mark.parametrize("help_option", ["-h", "--help"])
@pytest.mark.parametrize(
    "commands",
    [
        ("pytask",),
        ("pytask", "build"),
        ("pytask", "clean"),
        ("pytask", "collect"),
        ("pytask", "dag"),
        ("pytask", "markers"),
        ("pytask", "profile"),
    ],
)
def test_help_pages(runner, commands, help_option):
    result = runner.invoke(cli, [*commands, help_option])
    assert result.exit_code == ExitCode.OK
