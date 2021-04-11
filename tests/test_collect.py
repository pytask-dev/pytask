import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.collect import pytask_collect_node
from _pytask.config import IS_FILE_SYSTEM_CASE_SENSITIVE
from _pytask.exceptions import NodeNotCollectedError
from _pytask.session import Session
from pytask import main


@pytest.mark.end_to_end
def test_collect_filepathnode_with_relative_path(tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(depends_on, produces):
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Relative paths work.")

    session = main({"paths": tmp_path})

    assert session.collection_reports[0].successful
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
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == 3
    assert isinstance(session.collection_reports[0].exc_info[1], NodeNotCollectedError)


@pytest.mark.end_to_end
def test_collect_nodes_with_the_same_name(tmp_path):
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
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    tmp_path.joinpath("text.txt").write_text("in root")

    tmp_path.joinpath("sub").mkdir()
    tmp_path.joinpath("sub", "text.txt").write_text("in sub")

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert tmp_path.joinpath("out_0.txt").read_text() == "in root"
    assert tmp_path.joinpath("out_1.txt").read_text() == "in sub"


@pytest.mark.end_to_end
@pytest.mark.parametrize("path_extension", ["", "task_dummy.py"])
def test_collect_same_test_different_ways(tmp_path, path_extension):
    tmp_path.joinpath("task_dummy.py").write_text("def task_dummy(): pass")

    session = main({"paths": tmp_path.joinpath(path_extension)})

    assert session.exit_code == 0
    assert len(session.tasks) == 1


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "task_files, pattern, expected_collected_tasks",
    [
        (["dummy_task.py"], "*_task.py", 1),
        (["tasks_dummy.py"], "tasks_*", 1),
        (["dummy_tasks.py"], "*_tasks.py", 1),
        (["task_dummy.py", "tasks_dummy.py"], "None", 1),
        (["task_dummy.py", "tasks_dummy.py"], "tasks_*.py", 1),
        (
            ["task_dummy.py", "tasks_dummy.py"],
            "\n            task_*.py\n             tasks_*.py",
            2,
        ),
    ],
)
@pytest.mark.parametrize("config_name", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_collect_files_w_custom_file_name_pattern(
    tmp_path, config_name, task_files, pattern, expected_collected_tasks
):
    tmp_path.joinpath(config_name).write_text(f"[pytask]\ntask_files = {pattern}")

    for file in task_files:
        tmp_path.joinpath(file).write_text("def task_dummy(): pass")

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
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
    ],
)
def test_pytask_collect_node(session, path, node, expectation, expected):
    with expectation:
        result = pytask_collect_node(session, path, node)
        assert str(result.path) == str(expected)


@pytest.mark.unit
@pytest.mark.skipif(
    IS_FILE_SYSTEM_CASE_SENSITIVE, reason="Only works on case-insensitive file systems."
)
def test_pytask_collect_node_raises_warning_if_path_is_not_correctly_cased(tmp_path):
    session = Session({"check_casing_of_paths": True}, None)
    task_path = tmp_path / "task_example.py"
    real_node = tmp_path / "text.txt"
    real_node.touch()
    collected_node = tmp_path / "TeXt.TxT"

    with pytest.warns(UserWarning, match="The provided path of"):
        result = pytask_collect_node(session, task_path, collected_node)
        assert str(result.path) == str(real_node)


@pytest.mark.unit
def test_pytask_collect_node_does_not_raise_warning_if_path_is_not_normalized(tmp_path):
    session = Session({"check_casing_of_paths": True}, None)
    task_path = tmp_path / "task_example.py"
    real_node = tmp_path / "text.txt"
    collected_node = f"../{tmp_path.name}/text.txt"

    with pytest.warns(None) as record:
        result = pytask_collect_node(session, task_path, collected_node)
        assert str(result.path) == str(real_node)
        assert not record

    print("is case-sesn", IS_FILE_SYSTEM_CASE_SENSITIVE)
    print(Path(tmp_path, "ExA.Txt").resolve())

    Path(tmp_path, "exa.txt").touch()

    print(Path(tmp_path, "ExA.Txt").resolve())
    print("exists:", Path(tmp_path, "ExA.Txt").exists())

    raise Exception
