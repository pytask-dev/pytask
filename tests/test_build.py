import textwrap

import pytest
from pytask import cli


@pytest.mark.end_to_end
def test_execution_failed(runner, tmp_path):
    source = """
    def task_raises():
        raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == 1


@pytest.mark.end_to_end
def test_configuration_failed(runner, tmp_path):
    result = runner.invoke(cli, [tmp_path.joinpath("non_existent_path").as_posix()])
    assert result.exit_code == 2


@pytest.mark.end_to_end
def test_collection_failed(runner, tmp_path):
    source = """
    raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == 3


@pytest.mark.end_to_end
def test_resolving_dependencies_failed(runner, tmp_path):
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
    assert result.exit_code == 4
