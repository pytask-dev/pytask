from __future__ import annotations

import sys
import textwrap
import warnings
from pathlib import Path

import pytest
from _pytask.collect import _find_shortest_uniquely_identifiable_name_for_tasks
from _pytask.collect import pytask_collect_node
from _pytask.exceptions import NodeNotCollectedError
from _pytask.models import NodeInfo
from pytask import build
from pytask import cli
from pytask import CollectionOutcome
from pytask import ExitCode
from pytask import Session
from pytask import Task


@pytest.mark.end_to_end()
def test_collect_filepathnode_with_relative_path(tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_write_text(depends_on, produces):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Relative paths work.")

    session = build(paths=tmp_path)

    assert session.collection_reports[0].outcome == CollectionOutcome.SUCCESS
    assert tmp_path.joinpath("out.txt").read_text() == "Relative paths work."


@pytest.mark.end_to_end()
def test_collect_depends_on_that_is_not_str_or_path(tmp_path):
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
    assert "'@pytask.mark.depends_on'" in str(exc_info[1])


@pytest.mark.end_to_end()
def test_collect_produces_that_is_not_str_or_path(tmp_path):
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
    assert "'@pytask.mark.depends_on'" in str(exc_info[1])


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
            Session({"check_casing_of_paths": False}, None),
            Path(),
            NodeInfo("", (), Path.cwd() / "text.txt"),
            Path.cwd() / "text.txt",
            id="test with absolute string path",
        ),
        pytest.param(
            Session({"check_casing_of_paths": False}, None),
            Path(),
            NodeInfo("", (), 1),
            "1",
            id="test with python node",
        ),
    ],
)
def test_pytask_collect_node(session, path, node_info, expected):
    result = pytask_collect_node(session, path, node_info)
    if result is None:
        assert result is expected
    else:
        assert str(result.load()) == str(expected)


@pytest.mark.unit()
@pytest.mark.skipif(
    sys.platform != "win32", reason="Only works on case-insensitive file systems."
)
def test_pytask_collect_node_raises_error_if_path_is_not_correctly_cased(tmp_path):
    session = Session({"check_casing_of_paths": True}, None)
    task_path = tmp_path / "task_example.py"
    real_node = tmp_path / "text.txt"
    real_node.touch()
    collected_node = tmp_path / "TeXt.TxT"

    with pytest.raises(Exception, match="The provided path of"):
        pytask_collect_node(session, task_path, NodeInfo("", (), collected_node))


@pytest.mark.unit()
@pytest.mark.parametrize("is_absolute", [True, False])
def test_pytask_collect_node_does_not_raise_error_if_path_is_not_normalized(
    tmp_path, is_absolute
):
    session = Session({"check_casing_of_paths": True}, None)
    task_path = tmp_path / "task_example.py"
    real_node = tmp_path / "text.txt"

    collected_node = Path("..", tmp_path.name, "text.txt")
    if is_absolute:
        collected_node = tmp_path / collected_node

    with warnings.catch_warnings(record=True) as record:
        result = pytask_collect_node(
            session, task_path, NodeInfo("", (), collected_node)
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
def test_collect_string_product_with_task_decorator(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.task
    def task_write_text(produces="out.txt"):
        produces.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end()
def test_collect_string_product_as_function_default(runner, tmp_path):
    source = """
    def task_write_text(produces="out.txt"):
        produces.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()


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
def test_product_cannot_mix_different_product_types(tmp_path):
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
    assert "The task uses multiple ways" in str(report.exc_info[1])


@pytest.mark.end_to_end()
def test_depends_on_cannot_mix_different_definitions(tmp_path):
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
    assert "The task uses multiple" in str(report.exc_info[1])


@pytest.mark.end_to_end()
def test_deprecation_warning_for_strings_in_depends_on(runner, tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_write_text(depends_on, produces):
        produces.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert "FutureWarning" in result.output
    assert "Using strings to specify a dependency" in result.output
    assert "Using strings to specify a product" in result.output


@pytest.mark.end_to_end()
def test_setting_name_for_path_node_via_annotation(tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import Product, PathNode
    from typing import Any

    def task_example(
        path: Annotated[Path, Product, PathNode(name="product")] = Path("out.txt"),
    ) -> None:
        path.write_text("text")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    assert session.exit_code == ExitCode.OK
    product = session.tasks[0].produces["path"]
    assert product.name == "product"
