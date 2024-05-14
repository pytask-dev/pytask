from __future__ import annotations

import textwrap

import pytest
from pytask import ExitCode
from pytask import cli


@pytest.mark.end_to_end()
def test_execution_failed(runner, tmp_path):
    source = """
    def task_raises():
        raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED


@pytest.mark.end_to_end()
def test_configuration_failed(runner, tmp_path):
    result = runner.invoke(cli, [tmp_path.joinpath("non_existent_path").as_posix()])
    assert result.exit_code == ExitCode.CONFIGURATION_FAILED


@pytest.mark.end_to_end()
def test_collection_failed(runner, tmp_path):
    source = """
    raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED


@pytest.mark.end_to_end()
def test_building_dag_failed(runner, tmp_path):
    source = """
    from pathlib import Path

    def task_passes_1(in_path = Path("in.txt"), produces = Path("out.txt")): ...
    def task_passes_2(in_path = Path("out.txt"), produces = Path("in.txt")): ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.DAG_FAILED
