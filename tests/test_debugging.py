from __future__ import annotations

import os
import re
import sys
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813

import click
import pytest

from _pytask.debugging import _pdbcls_callback
from pytask import ExitCode
from pytask import cli

try:
    import pexpect
except ModuleNotFoundError:  # pragma: no cover
    IS_PEXPECT_INSTALLED = False
else:
    IS_PEXPECT_INSTALLED = True


def _escape_ansi(line):
    """Escape ANSI sequences produced by rich."""
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


@pytest.mark.parametrize(
    ("value", "expected", "expectation"),
    [
        (None, None, does_not_raise()),
        ("module:debugger", ("module", "debugger"), does_not_raise()),
        ("mod.submod:debugger", ("mod.submod", "debugger"), does_not_raise()),
        ("asd", None, pytest.raises(click.BadParameter)),
        ("asd:dasd:asdsa", None, pytest.raises(click.BadParameter)),
        (1, None, pytest.raises(click.BadParameter)),
    ],
)
def test_capture_callback(value, expected, expectation):
    with expectation:
        result = _pdbcls_callback(None, None, value)  # type: ignore[arg-type]
        assert result == expected


def _flush(child):
    if child.isalive():
        child.read()
        child.wait()
    assert not child.isalive()


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_post_mortem_on_error(tmp_path):
    source = """
    def task_example():
        a = 'I am in the debugger. '
        b = 'For real!'
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask --pdb {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p a + b;; continue")
    rest = child.read().decode("utf-8")
    assert "'I am in the debugger. For real!'" in rest
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_post_mortem_on_error_w_kwargs(tmp_path):
    source = """
    from pathlib import Path

    def task_example(path=Path("in.txt")):
        a = path.read_text()
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Stuck in the middle with you.")

    child = pexpect.spawn(f"pytask --pdb {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p a;; continue")
    rest = child.read().decode("utf-8")
    assert "Stuck in the middle with you" in rest
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_trace(tmp_path):
    source = """
    def task_example():
        i = 32345434
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask --trace {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("n;; p i;; p i + 1;; p i + 2;; continue")
    rest = child.read().decode("utf-8")
    assert all(str(i) in rest for i in (32345434, 32345435, 32345436))
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_trace_w_kwargs(tmp_path):
    source = """
    from pathlib import Path

    def task_example(path=Path("in.txt")):
        print(path.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("I want you back.")

    child = pexpect.spawn(f"pytask --trace {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("n;; continue")
    rest = child.read().decode("utf-8")
    assert "I want you back." in rest
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_breakpoint(tmp_path):
    source = """
    def task_example():
        i = 32345434
        breakpoint()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p i;; p i + 1;; p i + 2;; continue")
    rest = child.read().decode("utf-8")
    assert all(str(i) in rest for i in (32345434, 32345435, 32345436))
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_set_trace(tmp_path):
    source = """
    import pdb
    def task_example():
        i = 32345434
        pdb.set_trace()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect("Pdb")
    child.sendline("p i;; p i + 1;; p i + 2;; continue")
    rest = child.read().decode("utf-8")
    assert all(str(i) in rest for i in (32345434, 32345435, 32345436))
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_interaction_capturing_simple(tmp_path):  # pragma: no cover
    source = """
    import pdb
    def task_1():
        i = 0
        print("hello17")
        pdb.set_trace()
        i == 1
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect(r"task_1\(\)")
    child.expect("Pdb")
    child.sendline("n")
    # Python < 3.13 stops at the next statement already, while Python >= 3.13
    # first stops on the set_trace call itself and reaches this line after "n".
    child.expect(["i == 1", "assert 0"])
    child.expect("Pdb")
    child.sendline("c")
    rest = child.read().decode("utf-8")
    assert "AssertionError" in rest
    assert "1" in rest
    assert "failed" in rest
    assert "Failed" in rest
    assert "task_module.py" in rest
    assert "task_1" in rest
    assert "hello17" in rest  # out is captured
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_set_trace_kwargs(tmp_path):
    source = """
    import pdb
    def task_1():
        i = 0
        print("hello17")
        pdb.set_trace(header="== my_header ==")
        x = 3
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect("== my_header ==")
    assert "PDB set_trace" not in child.before.decode()  # type: ignore[union-attr]
    child.expect("Pdb")
    child.sendline("c")
    rest = child.read().decode("utf-8")
    assert "1" in rest
    assert "failed" in rest
    assert "Failed" in rest
    assert "task_module.py" in rest
    assert "task_1" in rest
    assert "hello17" in rest  # out is captured
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_set_trace_interception(tmp_path):
    source = """
    import pdb
    def task_1():
        pdb.set_trace()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect("task_1")
    child.expect("Pdb")
    child.sendline("q")
    rest = child.read().decode("utf8")
    assert "1" in rest
    assert "failed" in rest
    assert "Failed" in rest
    assert "reading from stdin while output" not in rest
    # Commented out since the traceback is not hidden. Exiting the debugger should end
    # the session without traceback.
    # assert "BdbQuit" not in rest
    assert "Quitting debugger" in rest
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_set_trace_capturing_afterwards(tmp_path):
    source = """
    import pdb
    def task_1():
        pdb.set_trace()
    def task_2():
        print("hello")
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect("task_1")
    child.sendline("c")
    child.expect("task_2")
    child.expect("Captured")
    child.expect("hello")
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_interaction_capturing_twice(tmp_path):  # pragma: no cover
    source = """
    import pdb
    def task_1():
        i = 0
        print("hello17")
        pdb.set_trace()
        x = 3
        print("hello18")
        pdb.set_trace()
        x = 4
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.expect(["PDB", "set_trace", r"\(IO-capturing", "turned", r"off\)"])
    child.expect("task_1")
    child.expect("Pdb")
    child.sendline("n")
    child.expect([r"x = 3", r'print\("hello18"\)'])
    child.expect("Pdb")
    child.sendline("c")
    child.expect(["PDB", "continue", r"\(IO-capturing", r"resumed\)"])
    child.expect(["PDB", "set_trace", r"\(IO-capturing", "turned", r"off\)"])
    child.expect("Pdb")
    child.sendline("n")
    child.expect([r"x = 4", "assert 0"])
    child.expect("Pdb")
    child.sendline("c")
    child.expect(["PDB", "continue", r"\(IO-capturing", r"resumed\)"])
    child.expect("task_1")
    child.expect("failed")
    rest = _escape_ansi(child.read().decode("utf8"))
    assert "Captured stdout during call" in rest
    assert "hello17" in rest  # out is captured
    assert "hello18" in rest  # out is captured
    assert "1  Failed" in rest
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_with_injected_do_debug(tmp_path):
    """Simulates pdbpp or pdbp, which injects Pdb into do_debug, and uses self.__class__
    in do_continue."""
    source = """
    import pdb

    count_continue = 0

    class CustomPdb(pdb.Pdb, object):

        def do_debug(self, arg):
            import sys
            import types
            do_debug_func = pdb.Pdb.do_debug
            newglobals = do_debug_func.__globals__.copy()
            newglobals['Pdb'] = self.__class__
            orig_do_debug = types.FunctionType(
                do_debug_func.__code__, newglobals,
                do_debug_func.__name__, do_debug_func.__defaults__,
            )
            return orig_do_debug(self, arg)

        do_debug.__doc__ = pdb.Pdb.do_debug.__doc__

        if hasattr(pdb.Pdb, "_create_recursive_debugger"):

            def _create_recursive_debugger(self):
                return self.__class__(
                    self.completekey,
                    self.stdin,
                    self.stdout,
                )

        def do_continue(self, *args, **kwargs):
            global count_continue
            count_continue += 1
            return super(CustomPdb, self).do_continue(*args, **kwargs)

    def foo():
        print("print_from_foo")

    def task_1():
        i = 0
        print("hello17")
        pdb.set_trace()
        x = 3
        print("hello18")
        assert count_continue == 2, "unexpected_failure: %d != 2" % count_continue
        raise Exception("expected_failure")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(
        f"pytask --pdbcls=task_module:CustomPdb {tmp_path.as_posix()}",
        env={"PATH": os.environ["PATH"], "PYTHONPATH": f"{tmp_path.as_posix()}"},
    )

    child.expect(["PDB", "set_trace", r"\(IO-capturing", "turned", r"off\)"])
    child.expect(r"\n\(Pdb")
    child.sendline("debug foo()")
    child.expect("ENTERING RECURSIVE DEBUGGER")
    child.expect(r"\n\(\(Pdb")
    child.sendline("c")
    child.expect("LEAVING RECURSIVE DEBUGGER")
    assert b"PDB continue" not in child.before  # type: ignore[operator]
    # No extra newline.
    assert child.before.endswith(b"c\r\nprint_from_foo\r\n")  # type: ignore[union-attr]

    # set_debug should not raise outcomes. Exit, if used recursively.
    child.sendline("debug 42")
    child.sendline("q")
    child.expect("LEAVING RECURSIVE DEBUGGER")
    assert b"ENTERING RECURSIVE DEBUGGER" in child.before  # type: ignore[operator]
    assert b"Quitting debugger" not in child.before  # type: ignore[operator]

    child.sendline("c")
    child.expect(["PDB", "continue", r"\(IO-capturing", r"resumed\)"])
    rest = _escape_ansi(child.read().decode("utf8"))
    assert "hello17" in rest  # out is captured
    assert "hello18" in rest  # out is captured
    assert "1" in rest
    assert "failed" in rest
    assert "Failed" in rest
    assert "AssertionError: unexpected_failure" not in rest
    assert "expected_failure" in rest
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_without_capture(tmp_path):
    source = """
    import pdb
    def task_1():
        pdb.set_trace()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask -s {tmp_path.as_posix()}")
    child.expect(r"PDB set_trace")
    child.expect("Pdb")
    child.sendline("c")
    child.expect(r"PDB continue")
    child.expect(["1", "succeeded"])
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_used_outside_task(tmp_path):
    source = """
    import pdb
    pdb.set_trace()
    x = 5
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    if sys.version_info >= (3, 13):
        child.expect("pdb.set_trace()")
        child.sendline("n")
    child.expect("x = 5")
    child.expect("Pdb")
    child.sendeof()
    _flush(child)


def test_printing_of_local_variables(tmp_path, runner):
    source = """
    def task_example():
        a = 1
        helper()

    def helper():
        b = 2
        raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--show-locals"])
    assert result.exit_code == ExitCode.FAILED

    captured = result.output
    assert " locals " in captured
    assert "a = 1" in captured
    assert "b = 2" in captured


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_set_trace_is_returned_after_pytask_finishes(tmp_path):
    """Motivates unconfiguring of pdb.set_trace."""
    source = f"""
    import pytask

    def test_function():
        pytask.build(paths={tmp_path.as_posix()!r})
        breakpoint()
    """
    tmp_path.joinpath("test_example.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytest {tmp_path.as_posix()}")
    child.expect("breakpoint()")
    child.sendline("c")
    rest = child.read().decode("utf8")
    assert "1 passed" in rest
    _flush(child)


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_pdb_with_task_that_returns(tmp_path, runner):
    source = """
    from typing import Annotated
    from pathlib import Path

    def task_example() -> Annotated[str, Path("data.txt")]:
        return "1"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--pdb"])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("data.txt").read_text() == "1"


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_trace_with_task_that_returns(tmp_path):
    source = """
    from typing import Annotated
    from pathlib import Path

    def task_example() -> Annotated[str, Path("data.txt")]:
        return "1"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    child = pexpect.spawn(f"pytask {tmp_path.as_posix()}")
    child.sendline("c")
    rest = child.read().decode("utf8")
    assert "1  Succeeded" in _escape_ansi(rest)
    assert tmp_path.joinpath("data.txt").read_text() == "1"
    _flush(child)
