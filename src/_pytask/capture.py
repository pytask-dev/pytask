"""Capture stdout and stderr during collection and execution.

This module implements the :class:`CaptureManager` plugin which allows for capturing in
three ways.

- fd (file descriptor) level capturing (default): All writes going to the operating
  system file descriptors 1 and 2 will be captured.
- sys level capturing: Only writes to Python files ``sys.stdout`` and ``sys.stderr``
  will be captured. No capturing of writes to file descriptors is performed.
- tee-sys capturing: Python writes to ``sys.stdout`` and ``sys.stderr`` will be
  captured, however the writes will also be passed-through to the actual ``sys.stdout``
  and ``sys.stderr``.


References
----------

- `Blog post on redirecting and file descriptors
  <https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python>`_.
- `The capture module in pytest
  <https://github.com/pytest-dev/pytest/blob/master/src/_pytest/capture.py>`_.
- `The debugging module in pytest
  <https://github.com/pytest-dev/pytest/blob/master/src/_pytest/debugging.py>`_.

"""
import contextlib
import functools
import io
import os
import sys
from tempfile import TemporaryFile
from typing import AnyStr
from typing import Generator
from typing import Generic
from typing import Iterator
from typing import Optional
from typing import TextIO
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

import click
from _pytask.config import hookimpl
from _pytask.nodes import MetaTask
from _pytask.shared import get_first_non_none_value

if TYPE_CHECKING:
    from typing_extensions import Literal

    _CaptureMethod = Literal["fd", "sys", "no", "tee-sys"]

if TYPE_CHECKING:
    if sys.version_info >= (3, 8):
        from typing import final as final
    else:
        from typing_extensions import final as final
elif sys.version_info >= (3, 8):
    from typing import final as final
else:

    def final(f):
        return f


@hookimpl
def pytask_extend_command_line_interface(cli):
    """Add CLI options for capturing output."""
    additional_parameters = [
        click.Option(
            ["--capture"],
            type=click.Choice(["fd", "no", "sys", "tee-sys"]),
            help="Per task capturing method.  [default: fd]",
        ),
        click.Option(["-s"], is_flag=True, help="Shortcut for --capture=no."),
        click.Option(
            ["--show-capture"],
            type=click.Choice(["no", "stdout", "stderr", "all"]),
            help=(
                "Choose which captured output should be shown for failed tasks.  "
                "[default: all]"
            ),
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
    """Parse configuration.

    Note that, ``-s`` is a shortcut for ``--capture=no``.

    """
    if config_from_cli.get("s"):
        config["capture"] = "no"
    else:
        config["capture"] = get_first_non_none_value(
            config_from_cli,
            config_from_file,
            key="capture",
            default="fd",
            callback=_capture_callback,
        )

    config["show_capture"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="show_capture",
        default="all",
        callback=_show_capture_callback,
    )


@hookimpl
def pytask_post_parse(config):
    """Initialize the CaptureManager."""
    if config["capture"] == "fd":
        _py36_windowsconsoleio_workaround(sys.stdout)
    _colorama_workaround()
    _readline_workaround()

    pluginmanager = config["pm"]
    capman = CaptureManager(config["capture"])
    pluginmanager.register(capman, "capturemanager")
    capman.stop_capturing()
    capman.start_capturing()
    capman.suspend()


def _capture_callback(x):
    """Validate the passed options for capturing output."""
    if x in [None, "None", "none"]:
        x = None
    elif x in ["fd", "no", "sys", "tee-sys"]:
        pass
    else:
        raise ValueError("'capture' can only be one of ['fd', 'no', 'sys', 'tee-sys'].")

    return x


def _show_capture_callback(x):
    """Validate the passed options for showing captured output."""
    if x in [None, "None", "none"]:
        x = None
    elif x in ["no", "stdout", "stderr", "all"]:
        pass
    else:
        raise ValueError(
            "'show_capture' must be one of ['no', 'stdout', 'stderr', 'all']."
        )

    return x


# Copied from pytest with slightly modified docstrings.


def _colorama_workaround() -> None:
    """Ensure colorama is imported so that it attaches to the correct stdio
    handles on Windows.

    colorama uses the terminal on import time. So if something does the
    first import of colorama while I/O capture is active, colorama will
    fail in various ways.

    """
    if sys.platform.startswith("win32"):
        try:
            import colorama  # noqa: F401
        except ImportError:
            pass


def _readline_workaround() -> None:
    """Ensure readline is imported so that it attaches to the correct stdio handles on
    Windows.

    Pdb uses readline support where available -- when not running from the Python
    prompt, the readline module is not imported until running the pdb REPL.  If running
    pytest with the ``--pdb`` option this means the readline module is not imported
    until after I/O capture has been started.

    This is a problem for pyreadline, which is often used to implement readline support
    on Windows, as it does not attach to the correct handles for stdout and/or stdin if
    they have been redirected by the FDCapture mechanism.  This workaround ensures that
    readline is imported before I/O capture is setup so that it can attach to the actual
    stdin/out for the console.

    See https://github.com/pytest-dev/pytest/pull/1281.

    """
    if sys.platform.startswith("win32"):
        try:
            import readline  # noqa: F401
        except ImportError:
            pass


def _py36_windowsconsoleio_workaround(stream: TextIO) -> None:
    """Workaround for Windows Unicode console handling on Python>=3.6.

    Python 3.6 implemented Unicode console handling for Windows. This works by
    reading/writing to the raw console handle using ``{Read,Write}ConsoleW``.

    The problem is that we are going to ``dup2`` over the stdio file descriptors when
    doing ``FDCapture`` and this will ``CloseHandle`` the handles used by Python to
    write to the console. Though there is still some weirdness and the console handle
    seems to only be closed randomly and not on the first call to ``CloseHandle``, or
    maybe it gets reopened with the same handle value when we suspend capturing.

    The workaround in this case will reopen stdio with a different fd which also means a
    different handle by replicating the logic in
    "Py_lifecycle.c:initstdio/create_stdio".

    Parameters
    ---------
    stream
        In practice ``sys.stdout`` or ``sys.stderr``, but given here as parameter for
        unit testing purposes.

    See https://github.com/pytest-dev/py/issues/103.

    """
    if not sys.platform.startswith("win32") or hasattr(sys, "pypy_version_info"):
        return

    # Bail out if ``stream`` doesn't seem like a proper ``io`` stream (#2666).
    if not hasattr(stream, "buffer"):  # type: ignore[unreachable]
        return

    buffered = hasattr(stream.buffer, "raw")
    raw_stdout = stream.buffer.raw if buffered else stream.buffer

    if not isinstance(raw_stdout, io._WindowsConsoleIO):  # type: ignore[attr-defined]
        return

    def _reopen_stdio(f, mode):
        if not buffered and mode[0] == "w":
            buffering = 0
        else:
            buffering = -1

        return io.TextIOWrapper(
            open(os.dup(f.fileno()), mode, buffering),  # type: ignore[arg-type]
            f.encoding,
            f.errors,
            f.newlines,
            f.line_buffering,
        )

    sys.stdin = _reopen_stdio(sys.stdin, "rb")
    sys.stdout = _reopen_stdio(sys.stdout, "wb")
    sys.stderr = _reopen_stdio(sys.stderr, "wb")


# IO Helpers.


class EncodedFile(io.TextIOWrapper):
    __slots__ = ()

    @property
    def name(self) -> str:
        # Ensure that file.name is a string. Workaround for a Python bug fixed in
        # >=3.7.4: https://bugs.python.org/issue36015
        return repr(self.buffer)

    @property
    def mode(self) -> str:
        # TextIOWrapper doesn't expose a mode, but at least some of our tests check it.
        return self.buffer.mode.replace("b", "")


class CaptureIO(io.TextIOWrapper):
    def __init__(self) -> None:
        super().__init__(io.BytesIO(), encoding="UTF-8", newline="", write_through=True)

    def getvalue(self) -> str:
        assert isinstance(self.buffer, io.BytesIO)
        return self.buffer.getvalue().decode("UTF-8")


class TeeCaptureIO(CaptureIO):
    def __init__(self, other: TextIO) -> None:
        self._other = other
        super().__init__()

    def write(self, s: str) -> int:
        super().write(s)
        return self._other.write(s)


class DontReadFromInput:
    """Class to disable reading from stdin while capturing is activated."""

    encoding = None

    def read(self, *_args):  # noqa: U101
        raise OSError(
            "pytest: reading from stdin while output is captured! Consider using `-s`."
        )

    readline = read
    readlines = read
    __next__ = read

    def __iter__(self):
        return self

    def fileno(self) -> int:
        raise io.UnsupportedOperation("redirected stdin is pseudofile, has no fileno()")

    def isatty(self) -> bool:
        return False

    def close(self) -> None:
        pass

    @property
    def buffer(self):
        return self


# Capture classes.


patchsysdict = {0: "stdin", 1: "stdout", 2: "stderr"}
"""Dict[int, str]: Map file descriptors to their names."""


class NoCapture:
    """Dummy class when capturing is disabled."""

    EMPTY_BUFFER = None
    __init__ = start = done = suspend = resume = lambda *_args: None  # noqa: U101


class SysCaptureBinary:
    """Capture IO to/from Python's buffer for stdin, stdout, and stderr.

    Instead of :class:`SysCapture`, this class produces bytes instead of text.

    """

    EMPTY_BUFFER = b""

    def __init__(self, fd: int, tmpfile=None, *, tee: bool = False) -> None:
        name = patchsysdict[fd]
        self._old = getattr(sys, name)
        self.name = name
        if tmpfile is None:
            if name == "stdin":
                tmpfile = DontReadFromInput()
            else:
                tmpfile = CaptureIO() if not tee else TeeCaptureIO(self._old)
        self.tmpfile = tmpfile
        self._state = "initialized"

    def repr(self, class_name: str) -> str:  # noqa: A003
        return "<{} {} _old={} _state={!r} tmpfile={!r}>".format(
            class_name,
            self.name,
            hasattr(self, "_old") and repr(self._old) or "<UNSET>",
            self._state,
            self.tmpfile,
        )

    def __repr__(self) -> str:
        return "<{} {} _old={} _state={!r} tmpfile={!r}>".format(
            self.__class__.__name__,
            self.name,
            hasattr(self, "_old") and repr(self._old) or "<UNSET>",
            self._state,
            self.tmpfile,
        )

    def _assert_state(self, op: str, states: Tuple[str, ...]) -> None:
        assert (
            self._state in states
        ), "cannot {} in state {!r}: expected one of {}".format(
            op, self._state, ", ".join(states)
        )

    def start(self) -> None:
        self._assert_state("start", ("initialized",))
        setattr(sys, self.name, self.tmpfile)
        self._state = "started"

    def snap(self):
        self._assert_state("snap", ("started", "suspended"))
        self.tmpfile.seek(0)
        res = self.tmpfile.buffer.read()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def done(self) -> None:
        self._assert_state("done", ("initialized", "started", "suspended", "done"))
        if self._state == "done":
            return
        setattr(sys, self.name, self._old)
        del self._old
        self.tmpfile.close()
        self._state = "done"

    def suspend(self) -> None:
        self._assert_state("suspend", ("started", "suspended"))
        setattr(sys, self.name, self._old)
        self._state = "suspended"

    def resume(self) -> None:
        self._assert_state("resume", ("started", "suspended"))
        if self._state == "started":
            return
        setattr(sys, self.name, self.tmpfile)
        self._state = "started"

    def writeorg(self, data) -> None:
        self._assert_state("writeorg", ("started", "suspended"))
        self._old.flush()
        self._old.buffer.write(data)
        self._old.buffer.flush()


class SysCapture(SysCaptureBinary):
    """Capture IO to/from Python's buffer for stdin, stdout, and stderr.

    Instead of :class:`SysCaptureBinary`, this class produces text instead of bytes.

    """

    EMPTY_BUFFER = ""  # type: ignore[assignment]

    def snap(self):
        res = self.tmpfile.getvalue()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def writeorg(self, data):
        self._assert_state("writeorg", ("started", "suspended"))
        self._old.write(data)
        self._old.flush()


class FDCaptureBinary:
    """Capture IO to/from a given OS-level file descriptor.

    snap() produces `bytes`.

    """

    EMPTY_BUFFER = b""

    def __init__(self, targetfd: int) -> None:
        self.targetfd = targetfd

        try:
            os.fstat(targetfd)
        except OSError:
            # FD capturing is conceptually simple -- create a temporary file, redirect
            # the FD to it, redirect back when done. But when the target FD is invalid
            # it throws a wrench into this lovely scheme.

            # Tests themselves shouldn't care if the FD is valid, FD capturing should
            # work regardless of external circumstances. So falling back to just sys
            # capturing is not a good option.

            # Further complications are the need to support suspend() and the
            # possibility of FD reuse (e.g. the tmpfile getting the very same target
            # FD). The following approach is robust, I believe.
            self.targetfd_invalid: Optional[int] = os.open(os.devnull, os.O_RDWR)
            os.dup2(self.targetfd_invalid, targetfd)
        else:
            self.targetfd_invalid = None
        self.targetfd_save = os.dup(targetfd)

        if targetfd == 0:
            self.tmpfile = open(os.devnull)
            self.syscapture = SysCapture(targetfd)
        else:
            self.tmpfile = EncodedFile(
                TemporaryFile(buffering=0),  # type: ignore[arg-type]
                encoding="utf-8",
                errors="replace",
                newline="",
                write_through=True,
            )
            if targetfd in patchsysdict:
                self.syscapture = SysCapture(targetfd, self.tmpfile)
            else:
                self.syscapture = NoCapture()

        self._state = "initialized"

    def __repr__(self) -> str:
        return "<{} {} oldfd={} _state={!r} tmpfile={!r}>".format(
            self.__class__.__name__,
            self.targetfd,
            self.targetfd_save,
            self._state,
            self.tmpfile,
        )

    def _assert_state(self, op: str, states: Tuple[str, ...]) -> None:
        assert (
            self._state in states
        ), "cannot {} in state {!r}: expected one of {}".format(
            op, self._state, ", ".join(states)
        )

    def start(self) -> None:
        """Start capturing on targetfd using memorized tmpfile."""
        self._assert_state("start", ("initialized",))
        os.dup2(self.tmpfile.fileno(), self.targetfd)
        self.syscapture.start()
        self._state = "started"

    def snap(self):
        self._assert_state("snap", ("started", "suspended"))
        self.tmpfile.seek(0)
        res = self.tmpfile.buffer.read()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def done(self) -> None:
        """Stop capturing, restore streams, return original capture file,
        seeked to position zero."""
        self._assert_state("done", ("initialized", "started", "suspended", "done"))
        if self._state == "done":
            return
        os.dup2(self.targetfd_save, self.targetfd)
        os.close(self.targetfd_save)
        if self.targetfd_invalid is not None:
            if self.targetfd_invalid != self.targetfd:
                os.close(self.targetfd)
            os.close(self.targetfd_invalid)
        self.syscapture.done()
        self.tmpfile.close()
        self._state = "done"

    def suspend(self) -> None:
        self._assert_state("suspend", ("started", "suspended"))
        if self._state == "suspended":
            return
        self.syscapture.suspend()
        os.dup2(self.targetfd_save, self.targetfd)
        self._state = "suspended"

    def resume(self) -> None:
        self._assert_state("resume", ("started", "suspended"))
        if self._state == "started":
            return
        self.syscapture.resume()
        os.dup2(self.tmpfile.fileno(), self.targetfd)
        self._state = "started"

    def writeorg(self, data):
        """Write to original file descriptor."""
        self._assert_state("writeorg", ("started", "suspended"))
        os.write(self.targetfd_save, data)


class FDCapture(FDCaptureBinary):
    """Capture IO to/from a given OS-level file descriptor.

    snap() produces text.

    """

    # Ignore type because it doesn't match the type in the superclass (bytes).
    EMPTY_BUFFER = ""  # type: ignore

    def snap(self):
        self._assert_state("snap", ("started", "suspended"))
        self.tmpfile.seek(0)
        res = self.tmpfile.read()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def writeorg(self, data):
        """Write to original file descriptor."""
        super().writeorg(data.encode("utf-8"))


# MultiCapture


@final
@functools.total_ordering
class CaptureResult(Generic[AnyStr]):
    """The result of :meth:`MultiCapture.readouterr` which wraps stdout and stderr.

    This class was a namedtuple, but due to mypy limitation [0]_ it could not be made
    generic, so was replaced by a regular class which tries to emulate the pertinent
    parts of a namedtuple. If the mypy limitation is ever lifted, can make it a
    namedtuple again.

    .. [0] https://github.com/python/mypy/issues/685

    """

    # Can't use slots in Python<3.5.3 due to https://bugs.python.org/issue31272
    if sys.version_info >= (3, 5, 3):
        __slots__ = ("out", "err")

    def __init__(self, out: AnyStr, err: AnyStr) -> None:
        self.out: AnyStr = out
        self.err: AnyStr = err

    def __len__(self) -> int:
        return 2

    def __iter__(self) -> Iterator[AnyStr]:
        return iter((self.out, self.err))

    def __getitem__(self, item: int) -> AnyStr:
        return tuple(self)[item]

    def _replace(
        self, *, out: Optional[AnyStr] = None, err: Optional[AnyStr] = None
    ) -> "CaptureResult[AnyStr]":
        return CaptureResult(
            out=self.out if out is None else out, err=self.err if err is None else err
        )

    def count(self, value: AnyStr) -> int:
        return tuple(self).count(value)

    def index(self, value) -> int:
        return tuple(self).index(value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (CaptureResult, tuple)):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, (CaptureResult, tuple)):
            return NotImplemented
        return tuple(self) < tuple(other)

    def __repr__(self) -> str:
        return f"CaptureResult(out={self.out!r}, err={self.err!r})"


class MultiCapture(Generic[AnyStr]):
    """The class which manages the buffers connected to each stream.

    The class is instantiated with buffers for ``stdin``, ``stdout`` and ``stderr``.
    Then, the instance provides convenient methods to control all buffers at once, like
    start and stop capturing and reading the ``stdout`` and ``stderr``.

    """

    _state = None
    _in_suspended = False

    def __init__(self, in_, out, err) -> None:
        self.in_ = in_
        self.out = out
        self.err = err

    def __repr__(self) -> str:
        return (
            "<MultiCapture out={!r} err={!r} in_={!r} _state={!r} "
            "_in_suspended={!r}>"
        ).format(
            self.out,
            self.err,
            self.in_,
            self._state,
            self._in_suspended,
        )

    def start_capturing(self) -> None:
        self._state = "started"
        if self.in_:
            self.in_.start()
        if self.out:
            self.out.start()
        if self.err:
            self.err.start()

    def pop_outerr_to_orig(self) -> Tuple[AnyStr, AnyStr]:
        """Pop current snapshot out/err capture and flush to orig streams."""
        out, err = self.readouterr()
        if out:
            self.out.writeorg(out)
        if err:
            self.err.writeorg(err)
        return out, err

    def suspend_capturing(self, in_: bool = False) -> None:
        self._state = "suspended"
        if self.out:
            self.out.suspend()
        if self.err:
            self.err.suspend()
        if in_ and self.in_:
            self.in_.suspend()
            self._in_suspended = True

    def resume_capturing(self) -> None:
        self._state = "started"
        if self.out:
            self.out.resume()
        if self.err:
            self.err.resume()
        if self._in_suspended:
            self.in_.resume()
            self._in_suspended = False

    def stop_capturing(self) -> None:
        """Stop capturing and reset capturing streams."""
        if self._state == "stopped":
            raise ValueError("was already stopped")
        self._state = "stopped"
        if self.out:
            self.out.done()
        if self.err:
            self.err.done()
        if self.in_:
            self.in_.done()

    def is_started(self) -> bool:
        """Whether actively capturing -- not suspended or stopped."""
        return self._state == "started"

    def readouterr(self) -> CaptureResult[AnyStr]:
        if self.out:
            out = self.out.snap()
        else:
            out = ""
        if self.err:
            err = self.err.snap()
        else:
            err = ""
        return CaptureResult(out, err)


def _get_multicapture(method: "_CaptureMethod") -> MultiCapture[str]:
    """Set up the MultiCapture class with the passed method.

    For each valid method, the function instantiates the :class:`MultiCapture` class
    with the specified buffers for ``stdin``, ``stdout``, and ``stderr``.

    """
    if method == "fd":
        return MultiCapture(in_=FDCapture(0), out=FDCapture(1), err=FDCapture(2))
    elif method == "sys":
        return MultiCapture(in_=SysCapture(0), out=SysCapture(1), err=SysCapture(2))
    elif method == "no":
        return MultiCapture(in_=None, out=None, err=None)
    elif method == "tee-sys":
        return MultiCapture(
            in_=None, out=SysCapture(1, tee=True), err=SysCapture(2, tee=True)
        )
    raise ValueError(f"unknown capturing method: {method!r}")


# Own implementation of the CaptureManager.


class CaptureManager:
    """The capture plugin.

    This class is the capture plugin which implements some hooks and provides an
    interface around :func:`_get_multicapture` and :class:`MultiCapture` adjusted to
    pytask.

    The class manages that the appropriate capture method is enabled/disabled during the
    execution phase (setup, call, teardown). After each of those points, the captured
    output is obtained and attached to the execution report.

    """

    def __init__(self, method: "_CaptureMethod") -> None:
        self._method = method
        self._capturing: Optional[MultiCapture[str]] = None

    def __repr__(self) -> str:
        return ("<CaptureManager _method={!r} _capturing={!r}>").format(
            self._method, self._capturing
        )

    def is_capturing(self) -> Union[str, bool]:
        return self._method != "no"

    def start_capturing(self) -> None:
        assert self._capturing is None
        self._capturing = _get_multicapture(self._method)
        self._capturing.start_capturing()

    def stop_capturing(self) -> None:
        if self._capturing is not None:
            self._capturing.pop_outerr_to_orig()
            self._capturing.stop_capturing()
            self._capturing = None

    def resume(self) -> None:
        # During teardown of the python process, and on rare occasions, capture
        # attributes can be `None` while trying to resume global capture.
        if self._capturing is not None:
            self._capturing.resume_capturing()

    def suspend(self, in_: bool = False) -> None:
        if self._capturing is not None:
            self._capturing.suspend_capturing(in_=in_)

    def read(self) -> CaptureResult[str]:
        assert self._capturing is not None
        return self._capturing.readouterr()

    # Helper context managers

    @contextlib.contextmanager
    def task_capture(self, when: str, task: MetaTask) -> Generator[None, None, None]:
        """Pipe captured stdout and stderr into report sections."""
        self.resume()

        try:
            yield
        finally:
            self.suspend(in_=False)

        out, err = self.read()
        task.add_report_section(when, "stdout", out)
        task.add_report_section(when, "stderr", err)

    # Hooks

    @hookimpl(hookwrapper=True)
    def pytask_execute_task_setup(self, task: MetaTask) -> Generator[None, None, None]:
        """Capture output during setup."""
        with self.task_capture("setup", task):
            yield

    @hookimpl(hookwrapper=True)
    def pytask_execute_task(self, task: MetaTask) -> Generator[None, None, None]:
        """Capture output during execution."""
        with self.task_capture("call", task):
            yield

    @hookimpl(hookwrapper=True)
    def pytask_execute_task_teardown(
        self, task: MetaTask
    ) -> Generator[None, None, None]:
        """Capture output during teardown."""
        with self.task_capture("teardown", task):
            yield
