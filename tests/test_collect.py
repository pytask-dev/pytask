import os
import textwrap

import pytest
from _pytask.exceptions import NodeNotCollectedError
from pytask import main


@pytest.mark.end_to_end
def test_collect_filepathnode_with_relative_path(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy():
        Path("out.txt").write_text(
            Path("in.txt").read_text()
        )
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Relative paths work.")

    os.chdir(tmp_path)
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

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert session.exit_code == 3
    assert isinstance(session.collection_reports[0].exc_info[1], NodeNotCollectedError)


@pytest.mark.end_to_end
def test_collect_nodes_with_the_same_name(tmp_path):
    """Nodes with the same filename, not path, are not mistaken for each other."""
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on("text.txt")
    @pytask.mark.produces("out_0.txt")
    def task_0():
        in_ = Path("text.txt").read_text()
        print(Path("text.txt").resolve())
        Path("out_0.txt").write_text(in_)

    @pytask.mark.depends_on("sub/text.txt")
    @pytask.mark.produces("out_1.txt")
    def task_1():
        in_ = Path("sub/text.txt").read_text()
        Path("out_1.txt").write_text(in_)
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    tmp_path.joinpath("text.txt").write_text("in root")

    tmp_path.joinpath("sub").mkdir()
    tmp_path.joinpath("sub", "text.txt").write_text("in sub")

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert tmp_path.joinpath("out_0.txt").read_text() == "in root"
    assert tmp_path.joinpath("out_1.txt").read_text() == "in sub"


@pytest.mark.end_to_end
@pytest.mark.parametrize("path_extension", ["", "task_dummy.py"])
def test_collect_same_test_different_ways(tmp_path, path_extension):
    source = """
    def task_dummy():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

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
    config = textwrap.dedent(
        f"""
        [pytask]
        task_files = {pattern}
        """
    )
    tmp_path.joinpath(config_name).write_text(config)

    source = """
    def task_dummy():
        pass
    """
    for file in task_files:
        tmp_path.joinpath(file).write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert len(session.tasks) == expected_collected_tasks
