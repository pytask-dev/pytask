import textwrap

from pytask.exceptions import NodeNotCollectedError
from pytask.main import main


def test_collect_filepathnode_with_relative_path(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.depends_on(Path("in.txt"))
    @pytask.mark.produces(Path("out.txt"))
    def task_dummy():
        Path(__file__).parent.joinpath("out.txt").write_text(
            Path(__file__).parent.joinpath("in.txt").read_text()
        )
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Relative paths work.")

    session = main({"paths": tmp_path})

    assert session.results[0]["success"]
    assert tmp_path.joinpath("out.txt").read_text() == "Relative paths work."


def test_collect_filepathnode_with_unknown_type(tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("text.txt")
    def task_with_non_path_dependency():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == 1
    assert isinstance(session.collection_reports[0]["value"], NodeNotCollectedError)
