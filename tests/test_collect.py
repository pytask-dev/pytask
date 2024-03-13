from __future__ import annotations

import sys
import textwrap
import warnings
from pathlib import Path

import pytest
from _pytask.collect import _find_shortest_uniquely_identifiable_name_for_tasks
from _pytask.collect import pytask_collect_node
from pytask import build
from pytask import cli
from pytask import CollectionOutcome
from pytask import ExitCode
from pytask import NodeInfo
from pytask import NodeNotCollectedError
from pytask import Session
from pytask import Task


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("depends_on", "produces"),
    [
        ("'in.txt'", "'out.txt'"),
        ("Path('in.txt')", "Path('out.txt')"),
    ],
)
def test_collect_file_with_relative_path(tmp_path, depends_on, produces):
    source = f"""
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on({depends_on})
    @pytask.mark.produces({produces})
    def task_write_text(depends_on, produces):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Relative paths work.")

    session = build(paths=tmp_path)

    assert session.collection_reports[0].outcome == CollectionOutcome.SUCCESS
    assert tmp_path.joinpath("out.txt").read_text() == "Relative paths work."


@pytest.mark.end_to_end()
def test_relative_path_of_path_node(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import Product, PathNode

    def task_example(
        in_path: Annotated[Path, PathNode(path=Path("in.txt"))],
        path: Annotated[Path, Product, PathNode(path=Path("out.txt"))],
    ) -> None:
        path.write_text("text")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end()
def test_collect_depends_on_that_is_not_str_or_path(capsys, tmp_path):
    """If a node cannot be parsed because unknown type, raise an error."""
    source = """
    import pytask

    @pytask.mark.depends_on(True)
    def task_with_non_path_dependency():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert session.collection_reports[0].outcome == CollectionOutcome.FAIL
    exc_info = session.collection_reports[0].exc_info
    assert isinstance(exc_info[1], NodeNotCollectedError)
    captured = capsys.readouterr().out
    assert "'@pytask.mark.depends_on'" in captured
    # Assert tracebacks are hidden.
    assert "_pytask/collect.py" not in captured


@pytest.mark.end_to_end()
def test_collect_produces_that_is_not_str_or_path(tmp_path, capsys):
    """If a node cannot be parsed because unknown type, raise an error."""
    source = """
    import pytask

    @pytask.mark.produces(True)
    def task_with_non_path_dependency():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert session.collection_reports[0].outcome == CollectionOutcome.FAIL
    exc_info = session.collection_reports[0].exc_info
    assert isinstance(exc_info[1], NodeNotCollectedError)
    captured = capsys.readouterr().out
    assert "'@pytask.mark.depends_on'" in captured


@pytest.mark.end_to_end()
def test_collect_nodes_with_the_same_name(runner, tmp_path):
    """Nodes with the same filename, not path, are not mistaken for each other."""
    source = """
    import pytask

    @pytask.mark.depends_on("text.txt")
    @pytask.mark.produces("out_0.txt")
    def task_0(depends_on, produces):
        produces.write_text(depends_on.read_text())

    @pytask.mark.depends_on("sub/text.txt")
    @pytask.mark.produces("out_1.txt")
    def task_1(depends_on, produces):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    tmp_path.joinpath("text.txt").write_text("in root")

    tmp_path.joinpath("sub").mkdir()
    tmp_path.joinpath("sub", "text.txt").write_text("in sub")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out_0.txt").read_text() == "in root"
    assert tmp_path.joinpath("out_1.txt").read_text() == "in sub"


@pytest.mark.end_to_end()
@pytest.mark.parametrize("path_extension", ["", "task_module.py"])
def test_collect_same_task_different_ways(tmp_path, path_extension):
    tmp_path.joinpath("task_module.py").write_text("def task_passes(): pass")

    session = build(paths=tmp_path.joinpath(path_extension))

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("task_files", "pattern", "expected_collected_tasks"),
    [
        (["example_task.py"], "'*_task.py'", 1),
        (["tasks_example.py"], "'tasks_*'", 1),
        (["example_tasks.py"], "'*_tasks.py'", 1),
        (["task_module.py", "tasks_example.py"], "'tasks_*.py'", 1),
        (["task_module.py", "tasks_example.py"], "['task_*.py', 'tasks_*.py']", 2),
    ],
)
def test_collect_files_w_custom_file_name_pattern(
    tmp_path, task_files, pattern, expected_collected_tasks
):
    tmp_path.joinpath("pyproject.toml").write_text(
        f"[tool.pytask.ini_options]\ntask_files = {pattern}"
    )

    for file in task_files:
        tmp_path.joinpath(file).write_text("def task_example(): pass")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == expected_collected_tasks


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("session", "path", "node_info", "expected"),
    [
        pytest.param(
            Session.from_config(
                {"check_casing_of_paths": False, "paths": (Path.cwd(),)}
            ),
            Path(),
            NodeInfo(
                arg_name="",
                path=(),
                value=Path.cwd() / "text.txt",
                task_path=Path.cwd() / "task_example.py",
                task_name="task_example",
            ),
            Path.cwd() / "text.txt",
            id="test with absolute string path",
        ),
        pytest.param(
            Session.from_config(
                {"check_casing_of_paths": False, "paths": (Path.cwd(),)}
            ),
            Path(),
            NodeInfo(
                arg_name="",
                path=(),
                value=1,
                task_path=Path.cwd() / "task_example.py",
                task_name="task_example",
            ),
            "1",
            id="test with python node",
        ),
    ],
)
def test_pytask_collect_node(session, path, node_info, expected):
    result = pytask_collect_node(session, path, node_info)
    assert str(result.load()) == str(expected)


@pytest.mark.unit()
@pytest.mark.skipif(
    sys.platform != "win32", reason="Only works on case-insensitive file systems."
)
def test_pytask_collect_node_raises_error_if_path_is_not_correctly_cased(tmp_path):
    session = Session.from_config({"check_casing_of_paths": True})
    real_node = tmp_path / "text.txt"
    real_node.touch()
    collected_node = tmp_path / "TeXt.TxT"

    with pytest.raises(Exception, match="The provided path of"):
        pytask_collect_node(
            session,
            tmp_path,
            NodeInfo(
                arg_name="",
                path=(),
                value=collected_node,
                task_path=tmp_path.joinpath("task_example.py"),
                task_name="task_example",
            ),
        )


@pytest.mark.unit()
@pytest.mark.parametrize("is_absolute", [True, False])
def test_pytask_collect_node_does_not_raise_error_if_path_is_not_normalized(
    tmp_path, is_absolute
):
    session = Session.from_config({"check_casing_of_paths": True, "paths": (tmp_path,)})
    real_node = tmp_path / "text.txt"

    collected_node = Path("..", tmp_path.name, "text.txt")
    if is_absolute:
        collected_node = tmp_path / collected_node

    with warnings.catch_warnings(record=True) as record:
        result = pytask_collect_node(
            session,
            tmp_path,
            NodeInfo(
                arg_name="",
                path=(),
                value=collected_node,
                task_path=tmp_path / "task_example.py",
                task_name="task_example",
            ),
        )
        assert not record

    assert str(result.path) == str(real_node)


@pytest.mark.unit()
def test_find_shortest_uniquely_identifiable_names_for_tasks(tmp_path):
    tasks = []
    expected = {}

    dir_identifiable_by_base_name = tmp_path.joinpath("identifiable_by_base_name")
    dir_identifiable_by_base_name.mkdir()
    path_identifiable_by_base_name = dir_identifiable_by_base_name.joinpath("t.py")

    for base_name in ("base_name_ident_0", "base_name_ident_1"):
        task = Task(
            base_name=base_name, path=path_identifiable_by_base_name, function=None
        )
        tasks.append(task)
        expected[task.name] = "t.py::" + base_name

    dir_identifiable_by_module_name = tmp_path.joinpath("identifiable_by_module")
    dir_identifiable_by_module_name.mkdir()

    for module in ("t.py", "m.py"):
        module_path = dir_identifiable_by_module_name / module
        task = Task(base_name="task_a", path=module_path, function=None)
        tasks.append(task)
        expected[task.name] = module + "::task_a"

    dir_identifiable_by_folder = tmp_path / "identifiable_by_folder"
    dir_identifiable_by_folder_a = dir_identifiable_by_folder / "a"
    dir_identifiable_by_folder_a.mkdir(parents=True)
    dir_identifiable_by_folder_b = dir_identifiable_by_folder / "b"
    dir_identifiable_by_folder_b.mkdir()

    for base_path in (dir_identifiable_by_folder_a, dir_identifiable_by_folder_b):
        module_path = base_path / "t.py"
        task = Task(base_name="task_t", path=module_path, function=None)
        tasks.append(task)
        expected[task.name] = base_path.name + "/t.py::task_t"

    result = _find_shortest_uniquely_identifiable_name_for_tasks(tasks)
    assert result == expected


@pytest.mark.end_to_end()
def test_collect_dependencies_from_args_if_depends_on_is_missing(tmp_path):
    source = """
    from pathlib import Path

    def task_example(path_in = Path("in.txt"), produces = Path("out.txt")):
        produces.write_text(path_in.read_text())
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("hello")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    assert session.tasks[0].depends_on["path_in"].path == tmp_path.joinpath("in.txt")


@pytest.mark.end_to_end()
def test_collect_tasks_from_modules_with_the_same_name(tmp_path):
    """We need to check that task modules can have the same name. See #373 and #374."""
    tmp_path.joinpath("a").mkdir()
    tmp_path.joinpath("b").mkdir()
    tmp_path.joinpath("a", "task_module.py").write_text("def task_a(): pass")
    tmp_path.joinpath("b", "task_module.py").write_text("def task_a(): pass")
    session = build(paths=tmp_path)
    assert len(session.collection_reports) == 2
    assert all(
        report.outcome == CollectionOutcome.SUCCESS
        for report in session.collection_reports
    )
    assert {
        report.node.function.__module__ for report in session.collection_reports
    } == {"a.task_module", "b.task_module"}


@pytest.mark.end_to_end()
def test_collect_module_name(tmp_path):
    """We need to add a task module to the sys.modules. See #373 and #374."""
    source = """
    # without this import, everything works fine
    from __future__ import annotations

    import dataclasses

    @dataclasses.dataclass
    class Data:
        x: int

    def task_my_task():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    session = build(paths=tmp_path)
    outcome = session.collection_reports[0].outcome
    assert outcome == CollectionOutcome.SUCCESS


@pytest.mark.end_to_end()
@pytest.mark.parametrize("decorator", ["", "@task"])
def test_collect_string_product_with_or_without_task_decorator(
    runner, tmp_path, decorator
):
    source = f"""
    from pytask import task

    {decorator}
    def task_write_text(produces="out.txt"):
        produces.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()
    assert "FutureWarning" in result.output


@pytest.mark.end_to_end()
def test_collect_string_product_raises_error_with_annotation(runner, tmp_path):
    """The string is not converted to a path."""
    source = """
    from pytask import Product
    from typing_extensions import Annotated

    def task_write_text(out: Annotated[str, Product] = "out.txt") -> None:
        out.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED


@pytest.mark.end_to_end()
def test_product_cannot_mix_different_product_types(tmp_path, capsys):
    source = """
    import pytask
    from typing_extensions import Annotated
    from pytask import Product
    from pathlib import Path

    @pytask.mark.produces("out_deco.txt")
    def task_example(
        path: Annotated[Path, Product], produces: Path = Path("out_sig.txt")
    ):
        ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert len(session.tasks) == 0
    report = session.collection_reports[0]
    assert report.outcome == CollectionOutcome.FAIL
    captured = capsys.readouterr().out
    assert "The task uses multiple ways" in captured


@pytest.mark.end_to_end()
def test_depends_on_cannot_mix_different_definitions(tmp_path, capsys):
    source = """
    import pytask
    from typing_extensions import Annotated
    from pytask import Product
    from pathlib import Path

    @pytask.mark.depends_on("input_1.txt")
    def task_example(
        depends_on: Path = "input_2.txt",
        path: Annotated[Path, Product] = Path("out.txt")
    ):
        ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input_1.txt").touch()
    tmp_path.joinpath("input_2.txt").touch()
    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert len(session.tasks) == 0
    report = session.collection_reports[0]
    assert report.outcome == CollectionOutcome.FAIL
    captured = capsys.readouterr().out
    assert "The task uses multiple" in captured


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("depends_on", "produces"),
    [("'in.txt'", "Path('out.txt')"), ("Path('in.txt')", "'out.txt'")],
)
def test_deprecation_warning_for_strings_in_former_decorator_args(
    runner, tmp_path, depends_on, produces
):
    source = f"""
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on({depends_on})
    @pytask.mark.produces({produces})
    def task_write_text(depends_on, produces):
        produces.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert "FutureWarning" in result.output


@pytest.mark.end_to_end()
def test_no_deprecation_warning_for_using_magic_produces(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path

    def task_write_text(depends_on, produces=Path("out.txt")):
        produces.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert "FutureWarning" not in result.output


@pytest.mark.end_to_end()
def test_setting_name_for_path_node_via_annotation(tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import Product, PathNode

    def task_example(
        path: Annotated[Path, Product, PathNode(path=Path("out.txt"), name="product")],
    ) -> None:
        path.write_text("text")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    assert session.exit_code == ExitCode.OK
    product = session.tasks[0].produces["path"]
    assert product.name == "product"


@pytest.mark.end_to_end()
def test_error_when_dependency_is_defined_in_kwargs_and_annotation(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import Product, PathNode
    from pytask import PythonNode

    @pytask.mark.task(kwargs={"in_": "world"})
    def task_example(
        in_: Annotated[str, PythonNode(name="string", value="hello")],
        path: Annotated[Path, Product, PathNode(path=Path("out.txt"), name="product")],
    ) -> None:
        path.write_text(in_)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert "ValueError: The value for the parameter 'in_'" in result.output


@pytest.mark.end_to_end()
def test_error_when_product_is_defined_in_kwargs_and_annotation(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import Product, PathNode

    node = PathNode(path=Path("out.txt"), name="product")

    @pytask.mark.task(kwargs={"path": node})
    def task_example(path: Annotated[Path, Product, node]) -> None:
        path.write_text("text")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert "ValueError: The value for the parameter 'path'" in result.output


@pytest.mark.end_to_end()
def test_error_when_using_kwargs_and_node_in_annotation(runner, tmp_path):
    source = """
    from pathlib import Path
    from pytask import task, Product
    from typing_extensions import Annotated

    @task(kwargs={"path": Path("file.txt")})
    def task_example(path: Annotated[Path, Path("file.txt"), Product]) -> None: ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "is defined twice" in result.output


@pytest.mark.parametrize(
    "node",
    [
        "Path(__file__).parent",
        "PathNode(path=Path(__file__).parent)",
        "PickleNode(path=Path(__file__).parent)",
    ],
)
def test_error_when_path_dependency_is_directory(runner, tmp_path, node):
    source = f"""
    from pathlib import Path
    from pytask import PickleNode, PathNode

    def task_example(path = {node}): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert all(i in result.output for i in ("only", "files", "are", "allowed"))


@pytest.mark.parametrize(
    "node",
    [
        "Path(__file__).parent",
        "PathNode(path=Path(__file__).parent)",
        "PickleNode(path=Path(__file__).parent)",
    ],
)
def test_error_when_path_product_is_directory(runner, tmp_path, node):
    source = f"""
    from pathlib import Path
    from pytask import PickleNode, Product, PathNode
    from typing_extensions import Annotated
    from typing import Any

    def task_example(path: Annotated[Any, Product] = {node}): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert all(i in result.output for i in ("only", "files", "are", "allowed"))


@pytest.mark.parametrize(
    "node",
    [
        "Path(__file__).parent / 'file.txt'",
        "PathNode(path=Path(__file__).parent / 'file.txt')",
        "PickleNode(path=Path(__file__).parent / 'file.txt')",
    ],
)
def test_default_name_of_path_nodes(tmp_path, node):
    source = f"""
    from pathlib import Path
    from pytask import PickleNode, Product, PathNode
    from typing_extensions import Annotated
    from typing import Any

    def task_example() -> Annotated[str, {node}]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    session = build(paths=tmp_path)
    assert session.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file.txt").exists()
    assert session.tasks[0].produces["return"].name == tmp_path.name + "/file.txt"


def test_error_when_return_annotation_cannot_be_parsed(runner, tmp_path):
    source = """
    from typing_extensions import Annotated

    def task_example() -> Annotated[int, 1]: ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "The return annotation of the task" in result.output


@pytest.mark.end_to_end()
def test_scheduling_w_mixed_priorities(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.try_last
    @pytask.mark.try_first
    def task_mixed(): pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Could not collect" in result.output
    assert "The task cannot have" in result.output


@pytest.mark.end_to_end()
def test_module_can_be_collected(runner, tmp_path):
    source = """
    from pytask import Task, TaskWithoutPath, mark

    class C:
        def __getattr__(self, name):
            return C()
    c = C()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "attr_that_definitely_does_not_exist" not in result.output


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    "second_node", ["PythonNode()", "PathNode(path=Path('a.txt'))"]
)
def test_error_with_multiple_dependency_annotations(runner, tmp_path, second_node):
    source = f"""
    from typing_extensions import Annotated
    from pytask import PythonNode, PathNode
    from pathlib import Path

    def task_example(
        dependency: Annotated[str, PythonNode(), {second_node}] = "hello"
    ) -> None: ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Parameter 'dependency' has multiple node annot" in result.output
