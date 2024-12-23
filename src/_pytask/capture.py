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
  <https://github.com/pytest-dev/pytest/blob/main/src/_pytest/capture.py>`_.
- `The debugging module in pytest
  <https://github.com/pytest-dev/pytest/blob/main/src/_pytest/debugging.py>`_.

"""

from __future__ import annotations

import abc
import contextlib
import io
import os
import sys
from io import UnsupportedOperation
from tempfile import TemporaryFile
from typing import TYPE_CHECKING
from typing import Any
from typing import AnyStr
from typing import BinaryIO
from typing import Generic
from typing import NamedTuple
from typing import TextIO
from typing import final

import click
from typing_extensions import Self

from _pytask.capture_utils import CaptureMethod
from _pytask.capture_utils import ShowCapture
from _pytask.click import EnumChoice
from _pytask.pluginmanager import hookimpl
from _pytask.shared import convert_to_enum

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterator
    from types import TracebackType

    from _pytask.node_protocols import PTask


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Add CLI options for capturing output."""
    additional_parameters = [
        click.Option(
            ["--capture"],
            type=EnumChoice(CaptureMethod),
            default=CaptureMethod.FD,
            help="Per task capturing method.",
        ),
        click.Option(
            ["-s"],
            is_flag=True,
            default=False,
            help="Shortcut for --capture=no.",
        ),
        click.Option(
            ["--show-capture"],
            type=EnumChoice(ShowCapture),
            default=ShowCapture.ALL,
            help="Choose which captured output should be shown for failed tasks.",
        ),
    ]
    cli.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse configuration.

    Note that, ``-s`` is a shortcut for ``--capture=no``.

    """
    config["capture"] = convert_to_enum(config["capture"], CaptureMethod)
    if config["s"]:
        config["capture"] = CaptureMethod.NO
    config["show_capture"] = convert_to_enum(config["show_capture"], ShowCapture)


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Initialize the CaptureManager."""
    pluginmanager = config["pm"]
    capman = CaptureManager(config["capture"])
    pluginmanager.register(capman, "capturemanager")
    capman.stop_capturing()
    capman.start_capturing()
    capman.suspend()


# Copied from pytest with slightly modified docstrings.


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


class DontReadFromInput(TextIO):
    """Class to disable reading from stdin while capturing is activated."""

    @property
    def encoding(self) -> str:
        return sys.__stdin__.encoding

    def read(self, size: int = -1) -> str:  # noqa: ARG002
        msg = (
            "pytask: reading from stdin while output is captured! Consider using `-s`."
        )
        raise OSError(msg)

    readline = read

    def __next__(self) -> str:
        return self.readline()

    def readlines(self, hint: int | None = -1) -> list[str]:  # noqa: ARG002
        msg = "reading from stdin while output is captured!  Consider using `-s`."
        raise OSError(msg)

    def __iter__(self) -> Iterator[str]:
        return self

    def fileno(self) -> int:
        msg = "redirected stdin is pseudofile, has no fileno()"
        raise UnsupportedOperation(msg)

    def flush(self) -> None:
        msg = "redirected stdin is pseudofile, has no flush()"
        raise UnsupportedOperation(msg)

    def isatty(self) -> bool:
        return False

    def close(self) -> None:
        pass

    def readable(self) -> bool:
        return False

    def seek(self, offset: int, whence: int = 0) -> int:  # noqa: ARG002
        msg = "Redirected stdin is pseudofile, has no seek(int)."
        raise UnsupportedOperation(msg)

    def seekable(self) -> bool:
        return False

    def tell(self) -> int:
        msg = "Redirected stdin is pseudofile, has no tell()."
        raise UnsupportedOperation(msg)

    def truncate(self, size: int | None = None) -> int:  # noqa: ARG002
        msg = "Cannot truncate stdin."
        raise UnsupportedOperation(msg)

    def write(self, data: str) -> int:  # noqa: ARG002
        msg = "Cannot write to stdin."
        raise UnsupportedOperation(msg)

    def writelines(self, *args: Any) -> None:  # noqa: ARG002
        msg = "Cannot write to stdin."
        raise UnsupportedOperation(msg)

    def writable(self) -> bool:
        return False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        type: type[BaseException] | None,  # noqa: A002
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    @property
    def buffer(self) -> BinaryIO:
        # The str/bytes doesn't actually matter in this type, so OK to fake.
        return self  # type: ignore[return-value]


# Capture classes.


class CaptureBase(abc.ABC, Generic[AnyStr]):
    EMPTY_BUFFER: AnyStr

    @abc.abstractmethod
    def __init__(self, fd: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def done(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def suspend(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def resume(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def writeorg(self, data: AnyStr) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def snap(self) -> AnyStr:
        raise NotImplementedError


patchsysdict = {0: "stdin", 1: "stdout", 2: "stderr"}
"""dict[int, str]: Map file descriptors to their names."""


class NoCapture(CaptureBase[str]):
    """Dummy class when capturing is disabled."""

    EMPTY_BUFFER = ""

    def __init__(self, fd: int) -> None:
        pass

    def start(self) -> None:
        pass

    def done(self) -> None:
        pass

    def suspend(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def snap(self) -> str:
        return ""

    def writeorg(self, data: str) -> None:
        pass


class SysCaptureBase(CaptureBase[AnyStr]):
    """Capture IO to/from Python's buffer for stdin, stdout, and stderr.

    Instead of :class:`SysCapture`, this class produces bytes instead of text.

    """

    def __init__(
        self,
        fd: int,
        tmpfile: TextIO | None = None,
        *,
        tee: bool = False,
    ) -> None:
        name = patchsysdict[fd]
        self._old: TextIO = getattr(sys, name)
        self.name = name
        if tmpfile is None:
            if name == "stdin":
                tmpfile = DontReadFromInput()
            else:
                tmpfile = CaptureIO() if not tee else TeeCaptureIO(self._old)
        self.tmpfile = tmpfile
        self._state = "initialized"

    def repr(self, class_name: str) -> str:
        return "<{} {} _old={} _state={!r} tmpfile={!r}>".format(
            class_name,
            self.name,
            (hasattr(self, "_old") and repr(self._old)) or "<UNSET>",
            self._state,
            self.tmpfile,
        )

    def __repr__(self) -> str:
        return "<{} {} _old={} _state={!r} tmpfile={!r}>".format(
            self.__class__.__name__,
            self.name,
            (hasattr(self, "_old") and repr(self._old)) or "<UNSET>",
            self._state,
            self.tmpfile,
        )

    def _assert_state(self, op: str, states: tuple[str, ...]) -> None:
        assert (
            self._state in states
        ), "cannot {} in state {!r}: expected one of {}".format(
            op, self._state, ", ".join(states)
        )

    def start(self) -> None:
        self._assert_state("start", ("initialized",))
        setattr(sys, self.name, self.tmpfile)
        self._state = "started"

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


class SysCaptureBinary(SysCaptureBase[bytes]):
    EMPTY_BUFFER = b""

    def snap(self) -> bytes:
        self._assert_state("snap", ("started", "suspended"))
        self.tmpfile.seek(0)
        res = self.tmpfile.buffer.read()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def writeorg(self, data: bytes) -> None:
        self._assert_state("writeorg", ("started", "suspended"))
        self._old.flush()
        self._old.buffer.write(data)
        self._old.buffer.flush()


class SysCapture(SysCaptureBase[str]):
    """Capture IO to/from Python's buffer for stdin, stdout, and stderr.

    Instead of :class:`SysCaptureBinary`, this class produces text instead of bytes.

    """

    EMPTY_BUFFER = ""

    def snap(self) -> str:
        self._assert_state("snap", ("started", "suspended"))
        assert isinstance(self.tmpfile, CaptureIO)
        res = self.tmpfile.getvalue()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def writeorg(self, data: str) -> None:
        self._assert_state("writeorg", ("started", "suspended"))
        self._old.write(data)
        self._old.flush()


class FDCaptureBase(CaptureBase[AnyStr]):
    """Capture IO to/from a given OS-level file descriptor.

    snap() produces `bytes`.

    """

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
            self.targetfd_invalid: int | None = os.open(os.devnull, os.O_RDWR)
            os.dup2(self.targetfd_invalid, targetfd)
        else:
            self.targetfd_invalid = None
        self.targetfd_save = os.dup(targetfd)

        if targetfd == 0:
            self.tmpfile = open(os.devnull, encoding="utf-8")  # noqa: SIM115, PTH123
            self.syscapture: CaptureBase[str] = SysCapture(targetfd)
        else:
            self.tmpfile = EncodedFile(
                TemporaryFile(buffering=0),  # noqa: SIM115
                encoding="utf-8",
                errors="replace",
                newline="",
                write_through=True,
            )
            if targetfd in patchsysdict:
                self.syscapture = SysCapture(targetfd, self.tmpfile)
            else:
                self.syscapture = NoCapture(targetfd)

        self._state = "initialized"

    def __repr__(self) -> str:
        return "<{} {} oldfd={} _state={!r} tmpfile={!r}>".format(  # noqa: UP032
            self.__class__.__name__,
            self.targetfd,
            self.targetfd_save,
            self._state,
            self.tmpfile,
        )

    def _assert_state(self, op: str, states: tuple[str, ...]) -> None:
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

    def done(self) -> None:
        """Stop capturing.

        Stop capturing, restore streams, return original capture file, sought to
        position zero.

        """
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


class FDCaptureBinary(FDCaptureBase[bytes]):
    """Capture IO to/from a given OS-level file descriptor.

    snap() produces `bytes`.
    """

    EMPTY_BUFFER = b""

    def snap(self) -> bytes:
        self._assert_state("snap", ("started", "suspended"))
        self.tmpfile.seek(0)
        res = self.tmpfile.buffer.read()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def writeorg(self, data: bytes) -> None:
        """Write to original file descriptor."""
        self._assert_state("writeorg", ("started", "suspended"))
        os.write(self.targetfd_save, data)


class FDCapture(FDCaptureBase[str]):
    """Capture IO to/from a given OS-level file descriptor.

    snap() produces text.

    """

    EMPTY_BUFFER = ""

    def snap(self) -> str:
        self._assert_state("snap", ("started", "suspended"))
        self.tmpfile.seek(0)
        res = self.tmpfile.read()
        self.tmpfile.seek(0)
        self.tmpfile.truncate()
        return res

    def writeorg(self, data: str) -> None:
        """Write to original file descriptor."""
        self._assert_state("writeorg", ("started", "suspended"))
        # Will be fixed by pytest. Use encoding of original stream
        os.write(self.targetfd_save, data.encode("utf-8"))


# MultiCapture


# Generic NamedTuple only supported since Python 3.11.
if sys.version_info >= (3, 11) or TYPE_CHECKING:

    @final
    class CaptureResult(NamedTuple, Generic[AnyStr]):
        """A class for capture results."""

        out: AnyStr
        err: AnyStr

else:
    import collections

    class CaptureResult(
        collections.namedtuple("CaptureResult", ["out", "err"]),  # noqa: PYI024
        Generic[AnyStr],
    ):
        """A class for capture results."""

        __slots__ = ()


class MultiCapture(Generic[AnyStr]):
    """The class which manages the buffers connected to each stream.

    The class is instantiated with buffers for ``stdin``, ``stdout`` and ``stderr``.
    Then, the instance provides convenient methods to control all buffers at once, like
    start and stop capturing and reading the ``stdout`` and ``stderr``.

    """

    _state = None
    _in_suspended = False

    def __init__(
        self,
        in_: CaptureBase[AnyStr] | None,
        out: CaptureBase[AnyStr] | None,
        err: CaptureBase[AnyStr] | None,
    ) -> None:
        self.in_: CaptureBase[AnyStr] | None = in_
        self.out: CaptureBase[AnyStr] | None = out
        self.err: CaptureBase[AnyStr] | None = err

    def __repr__(self) -> str:
        return (  # noqa: UP032
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

    def pop_outerr_to_orig(self) -> tuple[AnyStr, AnyStr]:
        """Pop current snapshot out/err capture and flush to orig streams."""
        out, err = self.readouterr()
        if out:
            self.out.writeorg(out)  # type: ignore[union-attr]
        if err:
            self.err.writeorg(err)  # type: ignore[union-attr]
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
            self.in_.resume()  # type: ignore[union-attr]
            self._in_suspended = False

    def stop_capturing(self) -> None:
        """Stop capturing and reset capturing streams."""
        if self._state == "stopped":
            msg = "was already stopped"
            raise ValueError(msg)
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
        out = self.out.snap() if self.out else ""
        err = self.err.snap() if self.err else ""
        # Will be fixed by pytest. This type error is real, need to fix.
        return CaptureResult(out, err)  # type: ignore[arg-type]


def _get_multicapture(method: CaptureMethod) -> MultiCapture[str]:
    """Set up the MultiCapture class with the passed method.

    For each valid method, the function instantiates the :class:`MultiCapture` class
    with the specified buffers for ``stdin``, ``stdout``, and ``stderr``.

    """
    if method == CaptureMethod.FD:
        return MultiCapture(in_=FDCapture(0), out=FDCapture(1), err=FDCapture(2))
    if method == CaptureMethod.SYS:
        return MultiCapture(in_=SysCapture(0), out=SysCapture(1), err=SysCapture(2))
    if method == CaptureMethod.NO:
        return MultiCapture(in_=None, out=None, err=None)
    if method == CaptureMethod.TEE_SYS:
        return MultiCapture(
            in_=None, out=SysCapture(1, tee=True), err=SysCapture(2, tee=True)
        )
    msg = f"unknown capturing method: {method!r}"
    raise ValueError(msg)


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

    def __init__(self, method: CaptureMethod) -> None:
        self._method = method
        self._capturing: MultiCapture[str] | None = None

    def __repr__(self) -> str:
        return ("<CaptureManager _method={!r} _capturing={!r}>").format(  # noqa: UP032
            self._method, self._capturing
        )

    def is_capturing(self) -> bool:
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
    def task_capture(self, when: str, task: PTask) -> Generator[None, None, None]:
        """Pipe captured stdout and stderr into report sections."""
        self.resume()

        try:
            yield
        finally:
            self.suspend(in_=False)

            out, err = self.read()
            if out:
                task.report_sections.append((when, "stdout", out))
            if err:
                task.report_sections.append((when, "stderr", err))

    # Hooks

    @hookimpl(wrapper=True)
    def pytask_execute_task_setup(self, task: PTask) -> Generator[None, None, None]:
        """Capture output during setup."""
        with self.task_capture("setup", task):
            return (yield)

    @hookimpl(wrapper=True)
    def pytask_execute_task(self, task: PTask) -> Generator[None, None, None]:
        """Capture output during execution."""
        with self.task_capture("call", task):
            return (yield)

    @hookimpl(wrapper=True)
    def pytask_execute_task_teardown(self, task: PTask) -> Generator[None, None, None]:
        """Capture output during teardown."""
        with self.task_capture("teardown", task):
            return (yield)

    @hookimpl(wrapper=True)
    def pytask_collect_log(self) -> Generator[None, None, None]:
        """Suspend capturing at the end of the collection.

        This hook needs to be here as long as the collection has no proper capturing. If
        ``pdb.set_trace`` stops the collection, continuation in ``do_continue`` enables
        the capture manager. Then, the collection status will be captured and displayed
        in the output of the first task.

        Here, we stop the capture manager before logging the final collection status.

        """
        self.suspend(in_=True)
        return (yield)
