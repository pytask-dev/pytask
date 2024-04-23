from __future__ import annotations

import pytest
from pytask import ExitCode
from pytask import __version__
from pytask import cli

from tests.conftest import run_in_subprocess


@pytest.mark.end_to_end()
def test_version_option():
    result = run_in_subprocess(("pytask", "--version"))
    assert "pytask, version " + __version__ in result.stdout


@pytest.mark.end_to_end()
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


@pytest.mark.end_to_end()
@pytest.mark.parametrize("config_section", ["pytask.ini_options", "pytask"])
def test_help_texts_are_modified_by_config(tmp_path, config_section):
    tmp_path.joinpath("pyproject.toml").write_text(
        f'[tool.{config_section}]\nshow_capture = "stdout"'
    )
    result = run_in_subprocess(("pytask", "build", "--help"), cwd=tmp_path)
    assert "[default:" in result.stdout
    assert " stdout]" in result.stdout


def test_precendence_of_new_to_old_section(tmp_path):
    tmp_path.joinpath("pyproject.toml").write_text(
        '[tool.pytask.ini_options]\nshow_capture = "stdout"\n\n'
        '[tool.pytask]\nshow_capture = "stderr"'
    )
    result = run_in_subprocess(("pytask", "build", "--help"), cwd=tmp_path)
    assert "[default:" in result.stdout
    assert " stderr]" in result.stdout
