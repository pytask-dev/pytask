"""Capture stdout and stderr during collection and execution.


References
----------

- <capture module in pytest
  <https://github.com/pytest-dev/pytest/blob/master/src/_pytest/capture.py>`
- <debugging module in pytest
  <https://github.com/pytest-dev/pytest/blob/master/src/_pytest/debugging.py>`

"""
import contextlib
import functools
import io
import os
import sys
from io import UnsupportedOperation
from tempfile import TemporaryFile
from typing import Any
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
from _pytask.shared import get_first_non_none_value
from _pytest.capture import _colorama_workaround
from _pytest.capture import _get_multicapture
from _pytest.capture import _py36_windowsconsoleio_workaround
from _pytest.capture import _readline_workaround
from _pytest.capture import CaptureIO
from _pytest.capture import CaptureResult
from _pytest.capture import DontReadFromInput
from _pytest.capture import EncodedFile
from _pytest.capture import FDCapture
from _pytest.capture import FDCaptureBinary
from _pytest.capture import MultiCapture
from _pytest.capture import NoCapture
from _pytest.capture import SysCapture
from _pytest.capture import SysCaptureBinary
from _pytest.capture import TeeCaptureIO

if TYPE_CHECKING:
    from typing_extensions import Literal

    _CaptureMethod = Literal["fd", "sys", "no", "tee-sys"]


@hookimpl
def pytask_extend_command_line_interface(cli):
    additional_parameters = [
        click.Option(
            ["--capture"],
            metavar="METHOD",
            type=click.Choice(["fd", "no", "sys", "tee-sys"]),
            help="Per task capturing method.  [default: fd]",
        ),
        click.Option(["-s"], is_flag=True, help="Shortcut for --capture=no"),
    ]
    click.commands["build"].params.extend(additional_parameters)


@hookimpl
def pytask_parse_config(config, config_from_cli, config_from_file):
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


@hookimpl
def pytask_post_parse(config):
    if config["capture"] == "fd":
        _py36_windowsconsoleio_workaround(sys.stdout)
    _colorama_workaround()
    _readline_workaround()

    pluginmanager = config["pm"]
    capman = CaptureManager(config["capture"])
    pluginmanager.register(capman, "capturemanager")


def _capture_callback(x):
    if x in [None, "None", "none"]:
        x = None
    elif x in ["fd", "no", "sys", "tee-sys"]:
        pass
    else:
        raise ValueError("'capture' can only be one of ['fd', 'no', 'sys', 'tee-sys'].")


class CaptureManager:
    """The capture plugin.

    Manages that the appropriate capture method is enabled/disabled during
    collection and each test phase (setup, call, teardown). After each of
    those points, the captured output is obtained and attached to the
    collection/runtest report.

    There are two levels of capture:

    * global: enabled by default and can be suppressed by the ``-s``
      option. This is always enabled/disabled during collection and each test
      phase.
    * fixture: when a test function or one of its fixture depend on the
      ``capsys`` or ``capfd`` fixtures. In this case special handling is
      needed to ensure the fixtures take precedence over the global capture.

    """

    def __init__(self, method: "_CaptureMethod") -> None:
        self._method = method
        self._global_capturing = None  # type: Optional[MultiCapture[str]]
        self._capture_fixture = None  # type: Optional[CaptureFixture[Any]]

    def __repr__(self) -> str:
        return "<CaptureManager _method={!r} _global_capturing={!r} _capture_fixture={!r}>".format(
            self._method, self._global_capturing, self._capture_fixture
        )

    def is_capturing(self) -> Union[str, bool]:
        if self.is_globally_capturing():
            return "global"
        if self._capture_fixture:
            return "fixture %s" % self._capture_fixture.request.fixturename
        return False

    # Global capturing control

    def is_globally_capturing(self) -> bool:
        return self._method != "no"

    def start_global_capturing(self) -> None:
        assert self._global_capturing is None
        self._global_capturing = _get_multicapture(self._method)
        self._global_capturing.start_capturing()

    def stop_global_capturing(self) -> None:
        if self._global_capturing is not None:
            self._global_capturing.pop_outerr_to_orig()
            self._global_capturing.stop_capturing()
            self._global_capturing = None

    def resume_global_capture(self) -> None:
        # During teardown of the python process, and on rare occasions, capture
        # attributes can be `None` while trying to resume global capture.
        if self._global_capturing is not None:
            self._global_capturing.resume_capturing()

    def suspend_global_capture(self, in_: bool = False) -> None:
        if self._global_capturing is not None:
            self._global_capturing.suspend_capturing(in_=in_)

    def suspend(self, in_: bool = False) -> None:
        # Need to undo local capsys-et-al if it exists before disabling global capture.
        self.suspend_fixture()
        self.suspend_global_capture(in_)

    def resume(self) -> None:
        self.resume_global_capture()
        self.resume_fixture()

    def read_global_capture(self) -> CaptureResult[str]:
        assert self._global_capturing is not None
        return self._global_capturing.readouterr()

    # Fixture Control

    def set_fixture(self, capture_fixture: "CaptureFixture[Any]") -> None:
        if self._capture_fixture:
            current_fixture = self._capture_fixture.request.fixturename
            requested_fixture = capture_fixture.request.fixturename
            capture_fixture.request.raiseerror(
                "cannot use {} and {} at the same time".format(
                    requested_fixture, current_fixture
                )
            )
        self._capture_fixture = capture_fixture

    def unset_fixture(self) -> None:
        self._capture_fixture = None

    def activate_fixture(self) -> None:
        """If the current item is using ``capsys`` or ``capfd``, activate
        them so they take precedence over the global capture."""
        if self._capture_fixture:
            self._capture_fixture._start()

    def deactivate_fixture(self) -> None:
        """Deactivate the ``capsys`` or ``capfd`` fixture of this item, if any."""
        if self._capture_fixture:
            self._capture_fixture.close()

    def suspend_fixture(self) -> None:
        if self._capture_fixture:
            self._capture_fixture._suspend()

    def resume_fixture(self) -> None:
        if self._capture_fixture:
            self._capture_fixture._resume()

    # Helper context managers

    @contextlib.contextmanager
    def global_and_fixture_disabled(self) -> Generator[None, None, None]:
        """Context manager to temporarily disable global and current fixture capturing."""
        do_fixture = self._capture_fixture and self._capture_fixture._is_started()
        if do_fixture:
            self.suspend_fixture()
        do_global = self._global_capturing and self._global_capturing.is_started()
        if do_global:
            self.suspend_global_capture()
        try:
            yield
        finally:
            if do_global:
                self.resume_global_capture()
            if do_fixture:
                self.resume_fixture()

    @contextlib.contextmanager
    def item_capture(self, when: str, item: Item) -> Generator[None, None, None]:
        self.resume_global_capture()
        self.activate_fixture()
        try:
            yield
        finally:
            self.deactivate_fixture()
            self.suspend_global_capture(in_=False)

        out, err = self.read_global_capture()
        item.add_report_section(when, "stdout", out)
        item.add_report_section(when, "stderr", err)

    # Hooks

    @hookimpl(hookwrapper=True)
    def pytest_make_collect_report(self, collector: Collector):
        if isinstance(collector, pytest.File):
            self.resume_global_capture()
            outcome = yield
            self.suspend_global_capture()
            out, err = self.read_global_capture()
            rep = outcome.get_result()
            if out:
                rep.sections.append(("Captured stdout", out))
            if err:
                rep.sections.append(("Captured stderr", err))
        else:
            yield

    @hookimpl(hookwrapper=True)
    def pytask_execute_task_setup(self, item: Item) -> Generator[None, None, None]:
        with self.item_capture("setup", item):
            yield

    @hookimpl(hookwrapper=True)
    def pytask_execute_task(self, item: Item) -> Generator[None, None, None]:
        with self.item_capture("call", item):
            yield

    @hookimpl(hookwrapper=True)
    def pytask_execute_task_teardown(self, item: Item) -> Generator[None, None, None]:
        with self.item_capture("teardown", item):
            yield

    # @hookimpl(tryfirst=True)
    # def pytest_keyboard_interrupt(self) -> None:
    #     self.stop_global_capturing()

    # @hookimpl(tryfirst=True)
    # def pytest_internalerror(self) -> None:
    #     self.stop_global_capturing()
