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

    assert session.exit_code == 2
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
