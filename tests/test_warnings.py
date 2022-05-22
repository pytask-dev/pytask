from __future__ import annotations

import textwrap

import pytest
from pytask import cli
from pytask import ExitCode
from pytask import main


@pytest.mark.parametrize(
    "disable_warnings",
    [pytest.param(True, marks=pytest.mark.filterwarnings("ignore:warning!!!")), False],
)
def test_disable_warnings_cli(tmp_path, runner, disable_warnings):
    source = """
    import warnings

    def task_example():
        warnings.warn("warning!!!")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    flag = ["--disable-warnings"] if disable_warnings else []
    result = runner.invoke(cli, [tmp_path.as_posix()] + flag)

    assert result.exit_code == ExitCode.OK
    assert ("Warnings" in result.output) is not disable_warnings
    assert ("warning!!!" in result.output) is not disable_warnings


@pytest.mark.parametrize(
    "disable_warnings",
    [pytest.param(True, marks=pytest.mark.filterwarnings("ignore:warning!!!")), False],
)
def test_disable_warnings(tmp_path, disable_warnings):
    source = """
    import warnings

    def task_example():
        warnings.warn("warning!!!")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path, "disable_warnings": disable_warnings})

    assert session.exit_code == ExitCode.OK
    if disable_warnings:
        assert session.warnings == []
    else:
        assert len(session.warnings) == 1
        assert "warning!!!" in session.warnings[0].message


@pytest.mark.parametrize("add_marker", [False, True])
def test_disable_warnings_with_mark(tmp_path, runner, add_marker):
    if add_marker:
        decorator = "@pytask.mark.filterwarnings('ignore:warning!!!')"
    else:
        decorator = ""

    source = f"""
    import pytask
    import warnings

    {decorator}
    def task_example():
        warnings.warn("warning!!!")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert ("Warnings" in result.output) is not add_marker
    assert ("warning!!!" in result.output) is not add_marker


@pytest.mark.parametrize(
    "disable_warnings",
    [pytest.param(True, marks=pytest.mark.filterwarnings("ignore:warning!!!")), False],
)
def test_disable_warnings_cli_collection(tmp_path, runner, disable_warnings):
    source = """
    import warnings

    warnings.warn("warning!!!")

    def task_example():
        ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    flag = ["--disable-warnings"] if disable_warnings else []
    result = runner.invoke(cli, [tmp_path.as_posix()] + flag)

    assert result.exit_code == ExitCode.OK
    assert ("Warnings" in result.output) is not disable_warnings
    assert ("warning!!!" in result.output) is not disable_warnings


@pytest.mark.parametrize("add_config", [False, True])
def test_disable_warnings_with_config(tmp_path, runner, add_config):
    if add_config:
        tmp_path.joinpath("pyproject.toml").write_text(
            "[tool.pytask.ini_options]\nfilterwarnings = ['ignore:warning!!!']"
        )

    source = """
    import warnings

    def task_example():
        warnings.warn("warning!!!")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert ("Warnings" in result.output) is not add_config
    assert ("warning!!!" in result.output) is not add_config


@pytest.mark.parametrize("warning", ["DeprecationWarning", "PendingDeprecationWarning"])
def test_deprecation_warnings_are_not_captured(tmp_path, runner, warning):
    source = f"""
    import warnings

    def task_example():
        warnings.warn("warning!!!", {warning})
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Warnings" not in result.output
    assert "warning!!!" not in result.output
