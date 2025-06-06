from __future__ import annotations

import subprocess
import textwrap

import pytest

from pytask import ExitCode
from tests.conftest import run_in_subprocess


@pytest.mark.end_to_end
@pytest.mark.parametrize("module_name", [True, False])
def test_add_new_hook_via_cli(tmp_path, module_name):
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

    if module_name:
        args = (
            "uv",
            "run",
            "python",
            "-m",
            "pytask",
            "build",
            "--hook-module",
            "hooks.hooks",
            "--help",
        )
    else:
        args = (
            "uv",
            "run",
            "pytask",
            "build",
            "--hook-module",
            "hooks/hooks.py",
            "--help",
        )

    result = run_in_subprocess(args, cwd=tmp_path)
    assert result.exit_code == ExitCode.OK
    assert "--new-option" in result.stdout


@pytest.mark.end_to_end
@pytest.mark.parametrize("module_name", [True, False])
def test_add_new_hook_via_config(tmp_path, module_name):
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\nhook_module = ['hooks/hooks.py']"
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

    if module_name:
        args = (
            "uv",
            "run",
            "--no-project",
            "python",
            "-m",
            "pytask",
            "build",
            "--help",
        )
    else:
        args = ("uv", "run", "--no-project", "pytask", "build", "--help")

    result = run_in_subprocess(args, cwd=tmp_path)
    assert result.exit_code == ExitCode.OK
    assert "--new-option" in result.stdout


@pytest.mark.end_to_end
def test_error_when_hook_module_path_does_not_exist(tmp_path):
    result = subprocess.run(  # noqa: PLW1510
        ("pytask", "build", "--hook-module", "hooks.py", "--help"),
        cwd=tmp_path,
        capture_output=True,
    )
    assert result.returncode == ExitCode.CONFIGURATION_FAILED
    assert b"Error: Invalid value for '--hook-module'" in result.stderr


@pytest.mark.end_to_end
def test_error_when_hook_module_module_does_not_exist(tmp_path):
    result = subprocess.run(  # noqa: PLW1510
        ("pytask", "build", "--hook-module", "hooks", "--help"),
        cwd=tmp_path,
        capture_output=True,
    )
    assert result.returncode == ExitCode.CONFIGURATION_FAILED
    assert b"Error: Invalid value for '--hook-module':" in result.stderr


@pytest.mark.end_to_end
def test_error_when_hook_module_is_no_iterable(tmp_path):
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\nhook_module = 'hooks'"
    )
    result = subprocess.run(  # noqa: PLW1510
        ("pytask", "build", "--help"), cwd=tmp_path, capture_output=True
    )
    assert result.returncode == ExitCode.CONFIGURATION_FAILED
    assert b"Error: Invalid value for '--hook-module':" in result.stderr
