import textwrap

import pytest
from _pytask.collect_command import _print_collected_tasks
from pytask import cli


class DummyClass:
    pass


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

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy.py>" in captured
    assert "<Function" in captured
    assert "task_dummy>" in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy.py>" in captured
    assert "<Function" in captured
    assert "task_dummy>" in captured
    assert "<Dependency" in captured
    assert "in.txt>" in captured
    assert "<Product" in captured
    assert "out.txt>" in captured


@pytest.mark.end_to_end
def test_collect_parametrized_tasks(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.parametrize("arg, produces", [(0, "out_0.txt"), (1, "out_1.txt")])
    def task_dummy(arg):
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy.py>" in captured
    assert "<Function" in captured
    assert "[0-out_0.txt]>" in captured
    assert "[1-out_1.txt]>" in captured


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

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy.py>" in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Function" in captured
    assert "task_dummy_2>" not in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-k", "_1", "--nodes"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy.py>" in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


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

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy.py>" in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Function" in captured
    assert "task_dummy_2>" not in captured

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "-m", "wip", "--nodes"]
    )

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy.py>" in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


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

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy_1.py>" in captured
    assert "task_dummy_2.py>" not in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Function" in captured
    assert "task_dummy_2>" not in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy_1.py>" in captured
    assert "task_dummy_2.py>" not in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


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

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy_1.py>" in captured
    assert "task_dummy_2.py>" not in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Function" in captured
    assert "task_dummy_2>" not in captured

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "--ignore", "task_dummy_2.py", "--nodes"]
    )

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_dummy_1.py>" in captured
    assert "task_dummy_2.py>" not in captured
    assert "<Function" in captured
    assert "task_dummy_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


@pytest.mark.unit
def test_print_collected_tasks_without_nodes(capsys):
    dictionary = {
        "path.py": {"task_dummy": {"depends_on": ["in.txt"], "produces": ["out.txt"]}}
    }

    _print_collected_tasks(dictionary, False)

    captured = capsys.readouterr().out

    assert "<Module path.py>" in captured
    assert "<Function" in captured
    assert "task_dummy>" in captured
    assert "<Dependency in.txt>" not in captured
    assert "<Product out.txt>" not in captured


@pytest.mark.unit
def test_print_collected_tasks_with_nodes(capsys):
    dictionary = {
        "path.py": {"task_dummy": {"depends_on": ["in.txt"], "produces": ["out.txt"]}}
    }

    _print_collected_tasks(dictionary, True)

    captured = capsys.readouterr().out

    assert "<Module path.py>" in captured
    assert "<Function" in captured
    assert "task_dummy>" in captured
    assert "<Dependency in.txt>" in captured
    assert "<Product out.txt>" in captured
