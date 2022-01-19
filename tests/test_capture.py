import contextlib
import io
import os
import subprocess
import sys
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from io import UnsupportedOperation
from typing import BinaryIO
from typing import Generator

import pytest
from _pytask import capture
from _pytask.capture import _capture_callback
from _pytask.capture import _get_multicapture
from _pytask.capture import _show_capture_callback
from _pytask.capture import CaptureManager
from _pytask.capture import CaptureResult
from _pytask.capture import MultiCapture
from _pytask.outcomes import ExitCode
from pytask import cli


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expected, expectation",
    [
        (None, None, does_not_raise()),
        ("None", None, does_not_raise()),
        ("none", None, does_not_raise()),
        ("fd", "fd", does_not_raise()),
        ("no", "no", does_not_raise()),
        ("sys", "sys", does_not_raise()),
        ("tee-sys", "tee-sys", does_not_raise()),
        ("asd", None, pytest.raises(ValueError)),
        (1, None, pytest.raises(ValueError)),
    ],
)
def test_capture_callback(value, expected, expectation):
    with expectation:
        result = _capture_callback(value)
        assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "value, expected, expectation",
    [
        (None, None, does_not_raise()),
        ("None", None, does_not_raise()),
        ("none", None, does_not_raise()),
        ("no", "no", does_not_raise()),
        ("stdout", "stdout", does_not_raise()),
        ("stderr", "stderr", does_not_raise()),
        ("all", "all", does_not_raise()),
        ("asd", None, pytest.raises(ValueError)),
        (1, None, pytest.raises(ValueError)),
    ],
)
def test_show_capture_callback(value, expected, expectation):
    with expectation:
        result = _show_capture_callback(value)
        assert result == expected


@pytest.mark.end_to_end
@pytest.mark.parametrize("show_capture", ["s", "no", "stdout", "stderr", "all"])
def test_show_capture(tmp_path, runner, show_capture):
    source = """
    import sys

    def task_show_capture():
        sys.stdout.write("xxxx")
        sys.stderr.write("zzzz")
        raise Exception
    """
    tmp_path.joinpath("task_show_capture.py").write_text(textwrap.dedent(source))

    cmd_arg = "-s" if show_capture == "s" else f"--show-capture={show_capture}"
    result = runner.invoke(cli, [tmp_path.as_posix(), cmd_arg])

    assert result.exit_code == ExitCode.FAILED

    if show_capture in ["no", "s"]:
        assert "Captured" not in result.output
    elif show_capture == "stdout":
        assert "Captured stdout" in result.output
        assert "xxxx" in result.output
        assert "Captured stderr" not in result.output
        # assert "zzzz" not in result.output
    elif show_capture == "stderr":
        assert "Captured stdout" not in result.output
        # assert "xxxx" not in result.output
        assert "Captured stderr" in result.output
        assert "zzzz" in result.output
    elif show_capture == "all":
        assert "Captured stdout" in result.output
        assert "xxxx" in result.output
        assert "Captured stderr" in result.output
        assert "zzzz" in result.output
    else:
        raise NotImplementedError


# Following tests are copied from pytest.

# note: py.io capture tests where copied from pylib 1.4.20.dev2 (rev 13d9af95547e)


def StdCaptureFD(
    out: bool = True, err: bool = True, in_: bool = True
) -> MultiCapture[str]:
    return capture.MultiCapture(
        in_=capture.FDCapture(0) if in_ else None,
        out=capture.FDCapture(1) if out else None,
        err=capture.FDCapture(2) if err else None,
    )


def StdCapture(
    out: bool = True, err: bool = True, in_: bool = True
) -> MultiCapture[str]:
    return capture.MultiCapture(
        in_=capture.SysCapture(0) if in_ else None,
        out=capture.SysCapture(1) if out else None,
        err=capture.SysCapture(2) if err else None,
    )


def TeeStdCapture(
    out: bool = True, err: bool = True, in_: bool = True
) -> MultiCapture[str]:
    return capture.MultiCapture(
        in_=capture.SysCapture(0, tee=True) if in_ else None,
        out=capture.SysCapture(1, tee=True) if out else None,
        err=capture.SysCapture(2, tee=True) if err else None,
    )


@pytest.mark.end_to_end
class TestCaptureManager:
    @pytest.mark.parametrize("method", ["no", "sys", "fd"])
    def test_capturing_basic_api(self, method):
        capouter = StdCaptureFD()
        old = sys.stdout, sys.stderr, sys.stdin
        try:
            capman = CaptureManager(method)
            capman.start_capturing()
            capman.suspend()
            outerr = capman.read()
            assert outerr == ("", "")
            capman.suspend()
            outerr = capman.read()
            assert outerr == ("", "")
            print("hello")
            capman.suspend()
            out, err = capman.read()
            if method == "no":
                assert old == (sys.stdout, sys.stderr, sys.stdin)
            else:
                assert not out
            capman.resume()
            print("hello")
            capman.suspend()
            out, err = capman.read()
            if method != "no":
                assert out == "hello\n"
            capman.stop_capturing()
        finally:
            capouter.stop_capturing()

    def test_init_capturing(self):
        capouter = StdCaptureFD()
        try:
            capman = CaptureManager("fd")
            capman.start_capturing()
            pytest.raises(AssertionError, capman.start_capturing)
            capman.stop_capturing()
        finally:
            capouter.stop_capturing()


@pytest.mark.end_to_end
@pytest.mark.parametrize("method", ["fd", "sys"])
def test_capturing_unicode(tmp_path, runner, method):
    obj = "'b\u00f6y'"
    source = f"""
    # taken from issue 227 from nosetests
    def task_unicode():
        import sys
        print(sys.stdout)
        print({obj})
    """
    tmp_path.joinpath("task_unicode.py").write_text(
        textwrap.dedent(source), encoding="utf-8"
    )

    result = runner.invoke(cli, [tmp_path.as_posix(), f"--capture={method}"])

    assert "1  Succeeded" in result.output
    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end
@pytest.mark.parametrize("method", ["fd", "sys"])
def test_capturing_bytes_in_utf8_encoding(tmp_path, runner, method):
    source = """
    def task_unicode():
        print('b\\u00f6y')
    """
    tmp_path.joinpath("task_unicode.py").write_text(
        textwrap.dedent(source), encoding="utf-8"
    )

    result = runner.invoke(cli, [tmp_path.as_posix(), f"--capture={method}"])

    assert "1  Succeeded" in result.output
    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end
@pytest.mark.xfail(strict=True, reason="pytask cannot capture during collection.")
def test_collect_capturing(tmp_path, runner):
    source = """
    import sys
    print("collect %s failure" % 13)
    sys.stderr.write("collect %s_stderr failure" % 13)
    import xyz42123
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    for content in [
        "Captured stdout",
        "collect 13 failure",
        "Captured stderr",
        "collect 13_stderr failure",
    ]:
        assert content in result.output


@pytest.mark.end_to_end
def test_capturing_outerr(tmp_path, runner):
    source = """
    import sys

    def task_capturing():
        print(42)
        sys.stderr.write(str(23))

    def task_capturing_error():
        print(1)
        sys.stderr.write(str(2))
        raise ValueError
    """
    tmp_path.joinpath("task_capturing_outerr.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert "│ F" in result.output
    assert "│ ." in result.output
    for content in [
        "───────────────────────────────── Failures ──────────────────────────────────",
        "task_capturing_error failed",
        "ValueError",
        "──────────────────────── Captured stdout during call ────────────────────────",
        "1",
        "──────────────────────── Captured stderr during call ────────────────────────",
        "2",
        "2  Collected tasks",
        "1  Succeeded",
        "1  Failed",
        "─────────── Failed in ",
        "seconds ────────",
    ]:
        assert content in result.output


@pytest.mark.end_to_end
def test_capture_badoutput_issue412(tmp_path, runner):
    source = """
    import os
    def task_func():
        omg = bytearray([1,129,1])
        os.write(1, omg)
        assert 0
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--capture=fd"])

    for content in [
        "task_func",
        "assert 0",
        "Captured",
        "1  Failed",
    ]:
        assert content in result.output


@pytest.mark.unit
class TestCaptureIO:
    def test_text(self):
        f = capture.CaptureIO()
        f.write("hello")
        s = f.getvalue()
        assert s == "hello"
        f.close()

    def test_unicode_and_str_mixture(self):
        f = capture.CaptureIO()
        f.write("\u00f6")
        pytest.raises(TypeError, f.write, b"hello")

    def test_write_bytes_to_buffer(self):
        """In python3, stdout / stderr are text io wrappers (exposing a buffer
        property of the underlying bytestream).  See issue #1407
        """
        f = capture.CaptureIO()
        f.buffer.write(b"foo\r\n")
        assert f.getvalue() == "foo\r\n"


@pytest.mark.unit
class TestTeeCaptureIO(TestCaptureIO):
    def test_text(self):
        sio = io.StringIO()
        f = capture.TeeCaptureIO(sio)
        f.write("hello")
        s1 = f.getvalue()
        assert s1 == "hello"
        s2 = sio.getvalue()
        assert s2 == s1
        f.close()
        sio.close()

    def test_unicode_and_str_mixture(self):
        sio = io.StringIO()
        f = capture.TeeCaptureIO(sio)
        f.write("\u00f6")
        pytest.raises(TypeError, f.write, b"hello")


@pytest.mark.integration
def test_dontreadfrominput():
    from _pytest.capture import DontReadFromInput

    f = DontReadFromInput()
    assert f.buffer is f
    assert not f.isatty()
    pytest.raises(OSError, f.read)
    pytest.raises(OSError, f.readlines)
    iter_f = iter(f)
    pytest.raises(OSError, next, iter_f)
    pytest.raises(UnsupportedOperation, f.fileno)
    f.close()  # just for completeness


@pytest.mark.unit
def test_captureresult() -> None:
    cr = CaptureResult("out", "err")
    assert len(cr) == 2
    assert cr.out == "out"
    assert cr.err == "err"
    out, err = cr
    assert out == "out"
    assert err == "err"
    assert cr[0] == "out"
    assert cr[1] == "err"
    assert cr == cr
    assert cr == CaptureResult("out", "err")
    assert cr != CaptureResult("wrong", "err")
    assert cr == ("out", "err")
    assert cr != ("out", "wrong")
    assert hash(cr) == hash(CaptureResult("out", "err"))
    assert hash(cr) == hash(("out", "err"))
    assert hash(cr) != hash(("out", "wrong"))
    assert cr < ("z",)
    assert cr < ("z", "b")
    assert cr < ("z", "b", "c")
    assert cr.count("err") == 1
    assert cr.count("wrong") == 0
    assert cr.index("err") == 1
    with pytest.raises(ValueError):
        assert cr.index("wrong") == 0
    assert next(iter(cr)) == "out"
    assert cr._replace(err="replaced") == ("out", "replaced")


@pytest.fixture()
def tmpfile(tmp_path) -> Generator[BinaryIO, None, None]:
    f = tmp_path.joinpath("task_module.py").open("wb+")
    yield f
    if not f.closed:
        f.close()


@contextlib.contextmanager
def lsof_check():
    pid = os.getpid()
    try:
        out = subprocess.check_output(("lsof", "-p", str(pid))).decode()
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as exc:
        # about UnicodeDecodeError, see note on pytester
        pytest.skip(f"could not run 'lsof' ({exc!r})")
    yield
    out2 = subprocess.check_output(("lsof", "-p", str(pid))).decode()
    len1 = len([x for x in out.split("\n") if "REG" in x])
    len2 = len([x for x in out2.split("\n") if "REG" in x])
    assert len2 < len1 + 3, out2


@pytest.mark.unit
class TestFDCapture:
    def test_simple(self, tmpfile):
        fd = tmpfile.fileno()
        cap = capture.FDCapture(fd)
        data = b"hello"
        os.write(fd, data)
        pytest.raises(AssertionError, cap.snap)
        cap.done()
        cap = capture.FDCapture(fd)
        cap.start()
        os.write(fd, data)
        s = cap.snap()
        cap.done()
        assert s == "hello"

    def test_simple_many(self, tmpfile):
        for _ in range(10):
            self.test_simple(tmpfile)

    def test_simple_many_check_open_files(self, tmp_path):
        with lsof_check():
            with tmp_path.joinpath("task_module.py").open("wb+") as tmpfile:
                self.test_simple_many(tmpfile)

    def test_simple_fail_second_start(self, tmpfile):
        fd = tmpfile.fileno()
        cap = capture.FDCapture(fd)
        cap.done()
        pytest.raises(AssertionError, cap.start)

    def test_stderr(self):
        cap = capture.FDCapture(2)
        cap.start()
        print("hello", file=sys.stderr)
        s = cap.snap()
        cap.done()
        assert s == "hello\n"

    def test_stdin(self):
        cap = capture.FDCapture(0)
        cap.start()
        x = os.read(0, 100).strip()
        cap.done()
        assert x == b""

    def test_writeorg(self, tmpfile):
        data1, data2 = b"foo", b"bar"
        cap = capture.FDCapture(tmpfile.fileno())
        cap.start()
        tmpfile.write(data1)
        tmpfile.flush()
        cap.writeorg(data2.decode("ascii"))
        scap = cap.snap()
        cap.done()
        assert scap == data1.decode("ascii")
        with open(tmpfile.name, "rb") as stmp_file:
            stmp = stmp_file.read()
            assert stmp == data2

    def test_simple_resume_suspend(self):
        with saved_fd(1):
            cap = capture.FDCapture(1)
            cap.start()
            data = b"hello"
            os.write(1, data)
            sys.stdout.write("whatever")
            s = cap.snap()
            assert s == "hellowhatever"
            cap.suspend()
            os.write(1, b"world")
            sys.stdout.write("qlwkej")
            assert not cap.snap()
            cap.resume()
            os.write(1, b"but now")
            sys.stdout.write(" yes\n")
            s = cap.snap()
            assert s == "but now yes\n"
            cap.suspend()
            cap.done()
            pytest.raises(AssertionError, cap.suspend)

            assert repr(cap) == (
                "<FDCapture 1 oldfd={} _state='done' tmpfile={!r}>".format(
                    cap.targetfd_save, cap.tmpfile
                )
            )
            # Should not crash with missing "_old".
            assert repr(cap.syscapture) == (
                "<SysCapture stdout _old=<UNSET> _state='done' tmpfile={!r}>".format(
                    cap.syscapture.tmpfile
                )
            )

    def test_capfd_sys_stdout_mode(self, capfd):  # noqa: U100
        assert "b" not in sys.stdout.mode


@contextlib.contextmanager
def saved_fd(fd):
    new_fd = os.dup(fd)
    try:
        yield
    finally:
        os.dup2(new_fd, fd)
        os.close(new_fd)


@pytest.mark.unit
class TestStdCapture:
    captureclass = staticmethod(StdCapture)

    @contextlib.contextmanager
    def getcapture(self, **kw):
        cap = self.__class__.captureclass(**kw)
        cap.start_capturing()
        try:
            yield cap
        finally:
            cap.stop_capturing()

    def test_capturing_done_simple(self):
        with self.getcapture() as cap:
            sys.stdout.write("hello")
            sys.stderr.write("world")
            out, err = cap.readouterr()
        assert out == "hello"
        assert err == "world"

    def test_capturing_reset_simple(self):
        with self.getcapture() as cap:
            print("hello world")
            sys.stderr.write("hello error\n")
            out, err = cap.readouterr()
        assert out == "hello world\n"
        assert err == "hello error\n"

    def test_capturing_readouterr(self):
        with self.getcapture() as cap:
            print("hello world")
            sys.stderr.write("hello error\n")
            out, err = cap.readouterr()
            assert out == "hello world\n"
            assert err == "hello error\n"
            sys.stderr.write("error2")
            out, err = cap.readouterr()
        assert err == "error2"

    def test_capture_results_accessible_by_attribute(self):
        with self.getcapture() as cap:
            sys.stdout.write("hello")
            sys.stderr.write("world")
            capture_result = cap.readouterr()
        assert capture_result.out == "hello"
        assert capture_result.err == "world"

    def test_capturing_readouterr_unicode(self):
        with self.getcapture() as cap:
            print("hxąć")
            out, err = cap.readouterr()
        assert out == "hxąć\n"

    def test_reset_twice_error(self):
        with self.getcapture() as cap:
            print("hello")
            out, err = cap.readouterr()
        pytest.raises(ValueError, cap.stop_capturing)
        assert out == "hello\n"
        assert not err

    def test_capturing_modify_sysouterr_in_between(self):
        oldout = sys.stdout
        olderr = sys.stderr
        with self.getcapture() as cap:
            sys.stdout.write("hello")
            sys.stderr.write("world")
            sys.stdout = capture.CaptureIO()
            sys.stderr = capture.CaptureIO()
            print("not seen")
            sys.stderr.write("not seen\n")
            out, err = cap.readouterr()
        assert out == "hello"
        assert err == "world"
        assert sys.stdout == oldout
        assert sys.stderr == olderr

    def test_capturing_error_recursive(self):
        with self.getcapture() as cap1:
            print("cap1")
            with self.getcapture() as cap2:
                print("cap2")
                out2, err2 = cap2.readouterr()
                out1, err1 = cap1.readouterr()
        assert out1 == "cap1\n"
        assert out2 == "cap2\n"

    def test_just_out_capture(self):
        with self.getcapture(out=True, err=False) as cap:
            sys.stdout.write("hello")
            sys.stderr.write("world")
            out, err = cap.readouterr()
        assert out == "hello"
        assert not err

    def test_just_err_capture(self):
        with self.getcapture(out=False, err=True) as cap:
            sys.stdout.write("hello")
            sys.stderr.write("world")
            out, err = cap.readouterr()
        assert err == "world"
        assert not out

    def test_stdin_restored(self):
        old = sys.stdin
        with self.getcapture(in_=True):
            newstdin = sys.stdin
        assert newstdin != sys.stdin
        assert sys.stdin is old

    def test_stdin_nulled_by_default(self):
        print("XXX this test may well hang instead of crashing")
        print("XXX which indicates an error in the underlying capturing")
        print("XXX mechanisms")
        with self.getcapture():
            pytest.raises(OSError, sys.stdin.read)


@pytest.mark.unit
class TestTeeStdCapture(TestStdCapture):
    captureclass = staticmethod(TeeStdCapture)

    def test_capturing_error_recursive(self):
        r"""For TeeStdCapture since we passthrough stderr/stdout, cap1
        should get all output, while cap2 should only get "cap2\n"."""

        with self.getcapture() as cap1:
            print("cap1")
            with self.getcapture() as cap2:
                print("cap2")
                out2, err2 = cap2.readouterr()
                out1, err1 = cap1.readouterr()
        assert out1 == "cap1\ncap2\n"
        assert out2 == "cap2\n"


@pytest.mark.unit
class TestStdCaptureFD(TestStdCapture):
    captureclass = staticmethod(StdCaptureFD)

    def test_simple_only_fd(self, tmp_path, runner):
        source = """
        import os
        def task_x():
            os.write(1, b"hello\\n")
            assert 0
        """
        tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
        result = runner.invoke(cli, [tmp_path.as_posix()])
        for content in [
            "task_x",
            "assert 0",
            "Captured stdout",
        ]:
            assert content in result.output

    def test_intermingling(self):
        with self.getcapture() as cap:
            os.write(1, b"1")
            sys.stdout.write(str(2))
            sys.stdout.flush()
            os.write(1, b"3")
            os.write(2, b"a")
            sys.stderr.write("b")
            sys.stderr.flush()
            os.write(2, b"c")
            out, err = cap.readouterr()
        assert out == "123"
        assert err == "abc"

    def test_many(self, capfd):  # noqa: U100
        with lsof_check():
            for _ in range(10):
                cap = StdCaptureFD()
                cap.start_capturing()
                cap.stop_capturing()


@pytest.mark.unit
class TestStdCaptureFDinvalidFD:
    def test_stdcapture_fd_invalid_fd(self, tmp_path, runner):
        source = """
        import os
        from fnmatch import fnmatch
        from _pytask import capture
        def StdCaptureFD(out=True, err=True, in_=True):
            return capture.MultiCapture(
                in_=capture.FDCapture(0) if in_ else None,
                out=capture.FDCapture(1) if out else None,
                err=capture.FDCapture(2) if err else None,
            )
        def task_stdout():
            os.close(1)
            cap = StdCaptureFD(out=True, err=False, in_=False)
            assert fnmatch(
                repr(cap.out), "<FDCapture 1 oldfd=* _state='initialized' tmpfile=*>"
            )
            cap.start_capturing()
            os.write(1, b"stdout")
            assert cap.readouterr() == ("stdout", "")
            cap.stop_capturing()
        def task_stderr():
            os.close(2)
            cap = StdCaptureFD(out=False, err=True, in_=False)
            assert fnmatch(
                repr(cap.err), "<FDCapture 2 oldfd=* _state='initialized' tmpfile=*>"
            )
            cap.start_capturing()
            os.write(2, b"stderr")
            assert cap.readouterr() == ("", "stderr")
            cap.stop_capturing()
        def task_stdin():
            os.close(0)
            cap = StdCaptureFD(out=False, err=False, in_=True)
            assert fnmatch(
                repr(cap.in_), "<FDCapture 0 oldfd=* _state='initialized' tmpfile=*>"
            )
            cap.stop_capturing()
        """
        tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

        result = runner.invoke(cli, [tmp_path.as_posix(), "--capture=fd"])
        assert result.exit_code == ExitCode.OK
        assert "3  Succeeded" in result.output

    def test_fdcapture_invalid_fd_with_fd_reuse(self, tmp_path):
        os.chdir(tmp_path)
        with saved_fd(1):
            os.close(1)
            cap = capture.FDCaptureBinary(1)
            cap.start()
            os.write(1, b"started")
            cap.suspend()
            os.write(1, b" suspended")
            cap.resume()
            os.write(1, b" resumed")
            assert cap.snap() == b"started resumed"
            cap.done()
            with pytest.raises(OSError):
                os.write(1, b"done")

    def test_fdcapture_invalid_fd_without_fd_reuse(self, tmp_path):
        os.chdir(tmp_path)
        with saved_fd(1), saved_fd(2):
            os.close(1)
            os.close(2)
            cap = capture.FDCaptureBinary(2)
            cap.start()
            os.write(2, b"started")
            cap.suspend()
            os.write(2, b" suspended")
            cap.resume()
            os.write(2, b" resumed")
            assert cap.snap() == b"started resumed"
            cap.done()
            with pytest.raises(OSError):
                os.write(2, b"done")


@pytest.mark.unit
def test__get_multicapture() -> None:
    assert isinstance(_get_multicapture("no"), MultiCapture)
    pytest.raises(ValueError, _get_multicapture, "unknown").match(
        r"^unknown capturing method: 'unknown'"
    )
