from __future__ import annotations

import pytest

from pytask import ExitCode
from pytask import __version__
from pytask import cli
from tests.conftest import run_in_subprocess


def test_version_option():
    result = run_in_subprocess(("pytask", "--version"))
    assert "pytask, version " + __version__ in result.stdout


@pytest.mark.parametrize("help_option", ["-h", "--help"])
@pytest.mark.parametrize(
    "commands",
    [
        (),
        ("build",),
        ("clean",),
        ("collect",),
        ("dag",),
        ("markers",),
        ("profile",),
    ],
)
def test_help_pages(runner, commands, help_option):
    result = runner.invoke(cli, [*commands, help_option])
    assert result.exit_code == ExitCode.OK


def test_help_texts_are_modified_by_config(runner, tmp_path):
    tmp_path.joinpath("pyproject.toml").write_text(
        '[tool.pytask.ini_options]\nshow_capture = "stdout"'
    )

    result = runner.invoke(
        cli,
        ["build", "--help", "--config", tmp_path.joinpath("pyproject.toml").as_posix()],
    )

    assert "[default: stdout]" in result.output
