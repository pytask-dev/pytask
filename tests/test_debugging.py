import sys
import textwrap

import pytest

try:
    import pexpect
except ModuleNotFoundError:
    pytestmark = pytest.mark.skip(reason="pexpect is not installed.")


@pytest.mark.end_to_end
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_post_mortem_on_error(tmp_path):
    source = """
    def task_dummy():
        a = 'I am in the debugger. '
        b = 'For real!'
        assert 0
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask --pdb {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p a + b;; continue")
    rest = child.read().decode("utf-8")
    assert "'I am in the debugger. For real!'" in rest


@pytest.mark.end_to_end
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_post_mortem_on_error_w_kwargs(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on(Path(__file__).parent / "in.txt")
    def task_dummy(depends_on):
        a = depends_on.read_text()
        assert 0
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Stuck in the middle with you.")

    child = pexpect.spawn(f"pytask --pdb {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p a;; continue")
    rest = child.read().decode("utf-8")
    assert "Stuck in the middle with you" in rest


@pytest.mark.end_to_end
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_trace(tmp_path):
    source = """
    def task_dummy():
        i = 32345434
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask --trace {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("n;; p i;; p i + 1;; p i + 2;; continue")
    rest = child.read().decode("utf-8")
    assert all(str(i) in rest for i in [32345434, 32345435, 32345436])


@pytest.mark.end_to_end
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_trace_w_kwargs(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on(Path(__file__).parent / "in.txt")
    def task_dummy(depends_on):
        print(depends_on.read_text())
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("I want you back.")

    child = pexpect.spawn(f"pytask --trace {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("n;; continue")
    rest = child.read().decode("utf-8")
    assert "I want you back." in rest


@pytest.mark.end_to_end
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_breakpoint(tmp_path):
    source = """
    def task_dummy():
        i = 32345434
        breakpoint()
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p i;; p i + 1;; p i + 2;; continue")
    rest = child.read().decode("utf-8")
    assert all(str(i) in rest for i in [32345434, 32345435, 32345436])


@pytest.mark.end_to_end
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_set_trace(tmp_path):
    source = """
    import pdb
    def task_dummy():
        i = 32345434
        pdb.set_trace()
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p i;; p i + 1;; p i + 2;; continue")
    rest = child.read().decode("utf-8")
    assert all(str(i) in rest for i in [32345434, 32345435, 32345436])
