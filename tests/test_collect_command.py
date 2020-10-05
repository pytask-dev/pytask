import textwrap

import pytest
from pytask import cli


@pytest.mark.end_to_end
def test_collect_task(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    assert "<Module" in result.output
    assert "task_dummy.py>" in result.output
    assert "<Function task_dummy>" in result.output

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    assert "<Module" in result.output
    assert "task_dummy.py>" in result.output
    assert "<Function task_dummy>" in result.output
    assert "<Dependency" in result.output
    assert "in.txt>" in result.output
    assert "<Product" in result.output
    assert "out.txt>" in result.output


@pytest.mark.end_to_end
def test_collect_task_with_expressions(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_dummy_1():
        pass

    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_dummy_2():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-k", "_1"])

    assert "<Module" in result.output
    assert "task_dummy.py>" in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Function task_dummy_2>" not in result.output

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-k", "_1", "--nodes"])

    assert "<Module" in result.output
    assert "task_dummy.py>" in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Dependency" in result.output
    assert "in_1.txt>" in result.output
    assert "<Product" in result.output
    assert "out_1.txt>" in result.output


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_collect_task_with_marker(runner, tmp_path, config_name):
    source = """
    import pytask

    @pytask.mark.wip
    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_dummy_1():
        pass

    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_dummy_2():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    config = """
    [pytask]
    markers =
        wip: A work-in-progress marker.
    """
    tmp_path.joinpath(config_name).write_text(textwrap.dedent(config))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-m", "wip"])

    assert "<Module" in result.output
    assert "task_dummy.py>" in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Function task_dummy_2>" not in result.output

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "-m", "wip", "--nodes"]
    )

    assert "<Module" in result.output
    assert "task_dummy.py>" in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Dependency" in result.output
    assert "in_1.txt>" in result.output
    assert "<Product" in result.output
    assert "out_1.txt>" in result.output


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_collect_task_with_ignore_from_config(runner, tmp_path, config_name):
    source = """
    import pytask

    @pytask.mark.wip
    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_dummy_1():
        pass
    """
    tmp_path.joinpath("task_dummy_1.py").write_text(textwrap.dedent(source))

    source = """
    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_dummy_2():
        pass
    """
    tmp_path.joinpath("task_dummy_2.py").write_text(textwrap.dedent(source))

    config = """
    [pytask]
    ignore = task_dummy_2.py
    """
    tmp_path.joinpath(config_name).write_text(textwrap.dedent(config))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    assert "<Module" in result.output
    assert "task_dummy_1.py>" in result.output
    assert "task_dummy_2.py>" not in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Function task_dummy_2>" not in result.output

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    assert "<Module" in result.output
    assert "task_dummy_1.py>" in result.output
    assert "task_dummy_2.py>" not in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Dependency" in result.output
    assert "in_1.txt>" in result.output
    assert "<Product" in result.output
    assert "out_1.txt>" in result.output


@pytest.mark.end_to_end
def test_collect_task_with_ignore_from_cli(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.wip
    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_dummy_1():
        pass
    """
    tmp_path.joinpath("task_dummy_1.py").write_text(textwrap.dedent(source))

    source = """
    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_dummy_2():
        pass
    """
    tmp_path.joinpath("task_dummy_2.py").write_text(textwrap.dedent(source))

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "--ignore", "task_dummy_2.py"]
    )

    assert "<Module" in result.output
    assert "task_dummy_1.py>" in result.output
    assert "task_dummy_2.py>" not in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Function task_dummy_2>" not in result.output

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "--ignore", "task_dummy_2.py", "--nodes"]
    )

    assert "<Module" in result.output
    assert "task_dummy_1.py>" in result.output
    assert "task_dummy_2.py>" not in result.output
    assert "<Function task_dummy_1>" in result.output
    assert "<Dependency" in result.output
    assert "in_1.txt>" in result.output
    assert "<Product" in result.output
    assert "out_1.txt>" in result.output
