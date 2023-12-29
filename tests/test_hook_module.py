from __future__ import annotations

import textwrap

from pytask import cli
from pytask import ExitCode


def test_add_new_hook_via_cli(runner, tmp_path):
    hooks = """
    import click
    from pytask import hookimpl

    @hookimpl
    def pytask_extend_command_line_interface(cli):
        print("Hello World!")
        cli.commands["build"].params.append(click.Option(["--new-option"]))
    """
    tmp_path.joinpath("hooks.py").write_text(textwrap.dedent(hooks))
    result = runner.invoke(
        cli,
        [
            "build",
            tmp_path.as_posix(),
            "--hook-module",
            tmp_path.joinpath("hooks.py").as_posix(),
            "--help",
        ],
    )
    assert result.exit_code == ExitCode.OK
    assert "--new-option" in result.output


def test_add_new_hook_via_config(runner, tmp_path):
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
    result = runner.invoke(cli, ["build", tmp_path.as_posix(), "--help"])
    assert result.exit_code == ExitCode.OK
    assert "--new-option" in result.output
