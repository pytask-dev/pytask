import textwrap
from pathlib import Path

import attr
import pytest
from _pytask.collect_command import _find_common_ancestor_of_all_nodes
from _pytask.collect_command import _print_collected_tasks
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from pytask import cli


@pytest.mark.end_to_end
def test_collect_task(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example>" in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example>" in captured
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
    def task_example(arg):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    captured = result.output.replace("\n", "").replace(" ", "").replace("\u2502", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "[0-out_0.txt]>" in captured
    assert "[1-out_1.txt]>" in captured


@pytest.mark.end_to_end
def test_collect_task_with_expressions(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in_1.txt")
    @pytask.mark.produces("out_1.txt")
    def task_example_1():
        pass

    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()
    tmp_path.joinpath("in_2.txt").touch()

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-k", "_1"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-k", "_1", "--nodes"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
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
    def task_example_1():
        pass

    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()

    config = """
    [pytask]
    markers =
        wip: A work-in-progress marker.
    """
    tmp_path.joinpath(config_name).write_text(textwrap.dedent(config))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "-m", "wip"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "-m", "wip", "--nodes"]
    )

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_module.py>" in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
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
    def task_example_1():
        pass
    """
    tmp_path.joinpath("task_example_1.py").write_text(textwrap.dedent(source))

    source = """
    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_example_2.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()

    config = """
    [pytask]
    ignore = task_example_2.py
    """
    tmp_path.joinpath(config_name).write_text(textwrap.dedent(config))

    result = runner.invoke(cli, ["collect", tmp_path.as_posix()])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(cli, ["collect", tmp_path.as_posix(), "--nodes"])

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
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
    def task_example_1():
        pass
    """
    tmp_path.joinpath("task_example_1.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_1.txt").touch()

    source = """
    @pytask.mark.depends_on("in_2.txt")
    @pytask.mark.produces("out_2.txt")
    def task_example_2():
        pass
    """
    tmp_path.joinpath("task_example_2.py").write_text(textwrap.dedent(source))

    result = runner.invoke(
        cli, ["collect", tmp_path.as_posix(), "--ignore", "task_example_2.py"]
    )

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Function" in captured
    assert "task_example_2>" not in captured

    result = runner.invoke(
        cli,
        ["collect", tmp_path.as_posix(), "--ignore", "task_example_2.py", "--nodes"],
    )

    captured = result.output.replace("\n", "").replace(" ", "")
    assert "<Module" in captured
    assert "task_example_1.py>" in captured
    assert "task_example_2.py>" not in captured
    assert "<Function" in captured
    assert "task_example_1>" in captured
    assert "<Dependency" in captured
    assert "in_1.txt>" in captured
    assert "<Product" in captured
    assert "out_1.txt>" in captured


@attr.s
class Node(MetaNode):
    path = attr.ib()

    def state(self):
        ...


def function():
    ...


@attr.s
class Task(MetaTask):
    base_name = attr.ib()
    path = attr.ib()
    function = attr.ib()
    depends_on = attr.ib()
    produces = attr.ib()

    def execute(self):
        ...

    def state(self):
        ...

    def add_report_section(self):
        ...


@pytest.mark.unit
def test_print_collected_tasks_without_nodes(capsys):
    dictionary = {
        "task_path.py": [
            Task(
                base_name="function",
                path=Path("task_path.py"),
                function=function,
                depends_on={0: Node("in.txt")},
                produces={0: Node("out.txt")},
            )
        ]
    }

    _print_collected_tasks(dictionary, False, "file", Path())

    captured = capsys.readouterr().out

    assert "<Module task_path.py>" in captured
    assert "<Function task_path.py::function>" in captured
    assert "<Dependency in.txt>" not in captured
    assert "<Product out.txt>" not in captured


@pytest.mark.unit
def test_print_collected_tasks_with_nodes(capsys):
    dictionary = {
        "task_path.py": [
            Task(
                base_name="function",
                path=Path("task_path.py"),
                function=function,
                depends_on={0: Node("in.txt")},
                produces={0: Node("out.txt")},
            )
        ]
    }

    _print_collected_tasks(dictionary, True, "file", Path())

    captured = capsys.readouterr().out

    assert "<Module task_path.py>" in captured
    assert "<Function task_path.py::function>" in captured
    assert "<Dependency in.txt>" in captured
    assert "<Product out.txt>" in captured


@pytest.mark.unit
@pytest.mark.parametrize("show_nodes, expected_add", [(False, "src"), (True, "..")])
def test_find_common_ancestor_of_all_nodes(show_nodes, expected_add):
    tasks = [
        Task(
            base_name="function",
            path=Path.cwd() / "src" / "task_path.py",
            function=function,
            depends_on={0: Node(Path.cwd() / "src" / "in.txt")},
            produces={0: Node(Path.cwd().joinpath("..", "bld", "out.txt").resolve())},
        )
    ]

    result = _find_common_ancestor_of_all_nodes(tasks, [Path.cwd() / "src"], show_nodes)
    assert result == Path.cwd().joinpath(expected_add).resolve()
