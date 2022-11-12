from __future__ import annotations

import sys
import textwrap
import warnings
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.collect import _find_shortest_uniquely_identifiable_name_for_tasks
from _pytask.collect import pytask_collect_node
from _pytask.exceptions import NodeNotCollectedError
from pytask import cli
from pytask import CollectionOutcome
from pytask import ExitCode
from pytask import main
from pytask import Session
from pytask import Task


@pytest.mark.end_to_end
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

    session = main({"paths": tmp_path})

    assert session.collection_reports[0].outcome == CollectionOutcome.SUCCESS
    assert tmp_path.joinpath("out.txt").read_text() == "Relative paths work."


@pytest.mark.end_to_end
def test_collect_filepathnode_with_unknown_type(tmp_path):
    """If a node cannot be parsed because unknown type, raise an error."""
    source = """
    import pytask

    @pytask.mark.depends_on(True)
    def task_with_non_path_dependency():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert session.collection_reports[0].outcome == CollectionOutcome.FAIL
    exc_info = session.collection_reports[0].exc_info
    assert isinstance(exc_info[1], NodeNotCollectedError)


@pytest.mark.end_to_end
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


@pytest.mark.end_to_end
@pytest.mark.parametrize("path_extension", ["", "task_module.py"])
def test_collect_same_test_different_ways(tmp_path, path_extension):
    tmp_path.joinpath("task_module.py").write_text("def task_passes(): pass")

    session = main({"paths": tmp_path.joinpath(path_extension)})

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "task_files, pattern, expected_collected_tasks",
    [
        (["example_task.py"], "'*_task.py'", 1),
        (["tasks_example.py"], "'tasks_*'", 1),
        (["example_tasks.py"], "'*_tasks.py'", 1),
        (["task_module.py", "tasks_example.py"], "'None'", 1),
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

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == expected_collected_tasks


@pytest.mark.unit
@pytest.mark.parametrize(
    "session, path, node, expectation, expected",
    [
        pytest.param(
            Session({"check_casing_of_paths": False}, None),
            Path(),
            Path.cwd() / "text.txt",
            does_not_raise(),
            Path.cwd() / "text.txt",
            id="test with absolute string path",
        ),
        pytest.param(
            Session({"check_casing_of_paths": False}, None),
            Path(),
            1,
            does_not_raise(),
            None,
            id="test cannot collect node",
        ),
    ],
)
def test_pytask_collect_node(session, path, node, expectation, expected):
    with expectation:
        result = pytask_collect_node(session, path, node)
        if result is None:
            assert result is expected
        else:
            assert str(result.path) == str(expected)


@pytest.mark.unit
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
        pytask_collect_node(session, task_path, collected_node)


@pytest.mark.unit
@pytest.mark.parametrize("is_absolute", [True, False])
def test_pytask_collect_node_does_not_raise_error_if_path_is_not_normalized(
    tmp_path, is_absolute
):
    session = Session({"check_casing_of_paths": True}, None)
    task_path = tmp_path / "task_example.py"
    real_node = tmp_path / "text.txt"

    collected_node = f"../{tmp_path.name}/text.txt"
    if is_absolute:
        collected_node = tmp_path / collected_node

    with warnings.catch_warnings(record=True) as record:
        result = pytask_collect_node(session, task_path, collected_node)
        assert not record

    assert str(result.path) == str(real_node)


@pytest.mark.unit
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
