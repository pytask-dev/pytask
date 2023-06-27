from __future__ import annotations

import textwrap

import pytest
from pytask import cli
from pytask import ExitCode


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
    # TODO: Should maybe fail because depends_on and produces are not used.
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_passes_1():
        pass

    @pytask.mark.depends_on("out.txt")
    @pytask.mark.produces("in.txt")
    def task_passes_2():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.DAG_FAILED
