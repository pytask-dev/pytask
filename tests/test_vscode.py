from __future__ import annotations

import os
import textwrap

import pytest
from pytask import ExitCode
from pytask import cli


@pytest.mark.end_to_end()
def test_vscode_collect_failed(runner, tmp_path):
    source = """
    raise Exception
    """
    os.environ["PYTASK_VSCODE"] = "6000"
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED


@pytest.mark.end_to_end()
def test_vscode_collect(runner, tmp_path):
    source = """
    def task_raises():
        return
    """
    os.environ["PYTASK_VSCODE"] = "6000"
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
def test_vscode_build(runner, tmp_path):
    source = """
    def task_example():
        return
    def task_raises():
        raise Exception
    """
    os.environ["PYTASK_VSCODE"] = "6000"
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
