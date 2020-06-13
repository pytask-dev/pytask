import sys
import textwrap

import pexpect
import pytest


@pytest.mark.end_to_end
@pytest.mark.skipif(sys.platform == "win32", reason="Cannot spawn on Windows.")
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
@pytest.mark.skipif(sys.platform == "win32", reason="Cannot spawn on Windows.")
def test_trace(tmp_path):
    source = """
    def task_dummy():
        i = 32345434
        assert 0
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask --trace {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("n;; p i;; p i + 1;; p i + 2;; continue")
    rest = child.read().decode("utf-8")
    assert all(str(i) in rest for i in [32345434, 32345435, 32345436])
