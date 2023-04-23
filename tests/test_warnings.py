from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest
from pytask import cli
from pytask import ExitCode
from pytask import main


@pytest.mark.end_to_end()
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
    result = runner.invoke(cli, [tmp_path.as_posix(), *flag])

    assert result.exit_code == ExitCode.OK
    assert ("Warnings" in result.output) is not disable_warnings
    assert ("warning!!!" in result.output) is not disable_warnings


@pytest.mark.end_to_end()
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


@pytest.mark.end_to_end()
@pytest.mark.parametrize("add_marker", [False, True])
def test_disable_warnings_with_mark(tmp_path, runner, add_marker):
    decorator = "@pytask.mark.filterwarnings('ignore:warning!!!')" if add_marker else ""

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


@pytest.mark.end_to_end()
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
    result = runner.invoke(cli, [tmp_path.as_posix(), *flag])

    assert result.exit_code == ExitCode.OK
    assert ("Warnings" in result.output) is not disable_warnings
    assert ("warning!!!" in result.output) is not disable_warnings


@pytest.mark.end_to_end()
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


@pytest.mark.end_to_end()
@pytest.mark.xfail(sys.platform == "win32", reason="See #293.")
@pytest.mark.parametrize("warning", ["DeprecationWarning", "PendingDeprecationWarning"])
def test_deprecation_warnings_are_not_captured(tmp_path, warning):
    path_to_warn_module = tmp_path.joinpath("warning.py")
    source = """
    import importlib.util
    import sys
    from pathlib import Path

    def task_example():
        spec = importlib.util.spec_from_file_location(
            "warning", Path(__file__).parent / "warning.py"
        )
        warning_module = importlib.util.module_from_spec(spec)
        sys.modules["warning"] = warning_module
        spec.loader.exec_module(warning_module)
        warning_module.warn_now()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    warn_module = f"""
    import warnings

    def warn_now():
        warnings.warn("warning!!!", {warning})
    """
    path_to_warn_module.write_text(textwrap.dedent(warn_module))

    # Cannot use runner since then warnings are not ignored by default.
    result = subprocess.run(("pytask"), cwd=tmp_path, capture_output=True)

    assert result.returncode == ExitCode.OK
    assert "Warnings" not in result.stdout.decode()
    assert "warning!!!" not in result.stdout.decode()


@pytest.mark.end_to_end()
def test_multiple_occurrences_of_warning_are_reduced(tmp_path, runner):
    source = """
    import warnings
    import pytask

    for i in range(10):

        @pytask.mark.task
        def task_example():
            warnings.warn("warning!!!")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Warnings" in result.output
    assert "warning!!!" in result.output
    # One occurrence is sometimes clipped.
    assert result.output.count("task_example") in (30, 31)
