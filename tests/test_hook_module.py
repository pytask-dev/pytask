from __future__ import annotations

import subprocess
import textwrap

from pytask import ExitCode


def test_add_new_hook_via_cli(tmp_path):
    hooks = """
    import click
    from pytask import hookimpl

    @hookimpl
    def pytask_extend_command_line_interface(cli):
        print("Hello World!")
        cli.commands["build"].params.append(click.Option(["--new-option"]))
    """
    tmp_path.joinpath("hooks.py").write_text(textwrap.dedent(hooks))
    result = subprocess.run(
        ("pytask", "build", "--hook-module", "hooks.py", "--help"),
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    assert result.returncode == ExitCode.OK
    assert "--new-option" in result.stdout.decode()


def test_add_new_hook_via_config(tmp_path):
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\nhook_module = ['hooks.py']"
    )

    hooks = """
    import click
    from pytask import hookimpl

    @hookimpl
    def pytask_extend_command_line_interface(cli):
        cli.commands["build"].params.append(click.Option(["--new-option"]))
    """
    tmp_path.joinpath("hooks.py").write_text(textwrap.dedent(hooks))
    result = subprocess.run(
        ("pytask", "build", tmp_path.as_posix(), "--help"),
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    assert result.returncode == ExitCode.OK
    assert "--new-option" in result.stdout.decode()


def test_error_when_hook_module_path_does_not_exist(tmp_path):
    result = subprocess.run(  # noqa: PLW1510
        ("pytask", "build", "--hook-module", "hooks.py", "--help"),
        cwd=tmp_path,
        capture_output=True,
    )
    assert result.returncode == ExitCode.CONFIGURATION_FAILED
    assert b"Error: Invalid value for '--hook-module'" in result.stderr


def test_error_when_hook_module_module_does_not_exist(tmp_path):
    result = subprocess.run(  # noqa: PLW1510
        ("pytask", "build", "--hook-module", "hooks", "--help"),
        cwd=tmp_path,
        capture_output=True,
    )
    assert result.returncode == ExitCode.FAILED
    assert b"ModuleNotFoundError: No module named 'hooks'" in result.stderr
