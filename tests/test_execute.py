import os
import textwrap

from pytask.main import main


def test_depends_on_and_produces_can_be_used_in_task(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(depends_on, produces):
        assert isinstance(depends_on, str) and isinstance(produces, str)

        Path(produces).write_text(Path(depends_on).read_text())
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Here I am. Once again.")

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert tmp_path.joinpath("out.txt").read_text() == "Here I am. Once again."
