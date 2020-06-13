import textwrap

import pytest
from pytask.main import main
from pytask.outcomes import SkippedAncestorFailed
from pytask.outcomes import SkippedUnchanged


@pytest.mark.end_to_end
def test_skip_unchanged(tmp_path):
    source = """
    def task_dummy():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})
    assert session.results[0]["success"]

    session = main({"paths": tmp_path})
    assert isinstance(session.results[0]["value"], SkippedUnchanged)


@pytest.mark.end_to_end
def test_skip_unchanged_w_dependencies_and_products(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.depends_on(Path(__file__).parent / "in.txt")
    @pytask.mark.produces(Path(__file__).parent / "out.txt")
    def task_dummy():
        in_ = Path(__file__).parent.joinpath("in.txt").read_text()
        Path(__file__).parent.joinpath("out.txt").write_text(in_)
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Original content of in.txt.")

    session = main({"paths": tmp_path})
    assert session.results[0]["success"]
    assert tmp_path.joinpath("out.txt").read_text() == "Original content of in.txt."

    session = main({"paths": tmp_path})
    assert isinstance(session.results[0]["value"], SkippedUnchanged)
    assert tmp_path.joinpath("out.txt").read_text() == "Original content of in.txt."


@pytest.mark.end_to_end
def test_skip_if_ancestor_failed(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.produces(Path(__file__).parent / "out.txt")
    def task_first():
        assert 0


    @pytask.mark.depends_on(Path(__file__).parent / "out.txt")
    def task_second():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})
    assert not session.results[0]["success"]
    assert isinstance(session.results[0]["value"], Exception)
    assert not session.results[1]["success"]
    assert isinstance(session.results[1]["value"], SkippedAncestorFailed)


def test_if_skip_decorator_is_applied(tmp_path):
    source = """
    import pytask
    from pathlib import Path


    @pytask.mark.skip
    @pytask.mark.produces(Path(__file__).parent / "out.txt")
    def task_first():
        assert 0


    @pytask.mark.depends_on(Path(__file__).parent / "out.txt")
    def task_second():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})
    assert not session.results[0]["success"]
    assert isinstance(session.results[0]["value"], Exception)
    assert not session.results[1]["success"]
    assert isinstance(session.results[1]["value"], SkippedAncestorFailed)
