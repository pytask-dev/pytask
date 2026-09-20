from __future__ import annotations

import sys
import textwrap

import pytest

from pytask import ExitCode
from pytask import cli
from tests.conftest import enter_directory
from tests.conftest import run_in_subprocess


@pytest.mark.parametrize("hook_location", ["hooks/hooks.py", "hooks.hooks"])
def test_add_new_hook_via_cli(tmp_path, hook_location):
    hooks = """
    import click
    from pytask import hookimpl

    @hookimpl
    def pytask_extend_command_line_interface(cli):
        print("Hello World!")
        cli.commands["build"].params.append(click.Option(["--new-option"]))
    """
    tmp_path.joinpath("hooks").mkdir()
    tmp_path.joinpath("hooks", "hooks.py").write_text(textwrap.dedent(hooks))

    args = (
        sys.executable,
        "-m",
        "pytask",
        "build",
        "--hook-module",
        hook_location,
        "--help",
    )
    result = run_in_subprocess(args, cwd=tmp_path)
    assert result.exit_code == ExitCode.OK
    assert "--new-option" in result.stdout


@pytest.mark.parametrize("hook_location", ["hooks/hooks.py", "hooks.hooks"])
def test_add_new_hook_via_config(tmp_path, hook_location):
    tmp_path.joinpath("pyproject.toml").write_text(
        f"[tool.pytask.ini_options]\nhook_module = ['{hook_location}']"
    )

    hooks = """
    import click
    from pytask import hookimpl

    @hookimpl
    def pytask_extend_command_line_interface(cli):
        cli.commands["build"].params.append(click.Option(["--new-option"]))
    """
    tmp_path.joinpath("hooks").mkdir()
    tmp_path.joinpath("hooks", "hooks.py").write_text(textwrap.dedent(hooks))

    args = (sys.executable, "-m", "pytask", "build", "--help")

    result = run_in_subprocess(args, cwd=tmp_path)
    assert result.exit_code == ExitCode.OK
    assert "--new-option" in result.stdout


def test_error_when_hook_module_path_does_not_exist(tmp_path, runner):
    with enter_directory(tmp_path):
        result = runner.invoke(cli, ["build", "--hook-module", "hooks.py", "--help"])

    assert result.exit_code == ExitCode.CONFIGURATION_FAILED
    assert "Error: Invalid value for '--hook-module'" in result.output


def test_error_when_hook_module_module_does_not_exist(tmp_path, runner):
    with enter_directory(tmp_path):
        result = runner.invoke(cli, ["build", "--hook-module", "hooks", "--help"])

    assert result.exit_code == ExitCode.CONFIGURATION_FAILED
    assert "Error: Invalid value for '--hook-module':" in result.output


def test_error_when_hook_module_is_no_iterable(tmp_path, runner):
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\nhook_module = 'hooks'"
    )
    with enter_directory(tmp_path):
        result = runner.invoke(cli, ["build", "--help"])

    assert result.exit_code == ExitCode.CONFIGURATION_FAILED
    assert "Error: Invalid value for '--hook-module':" in result.output
