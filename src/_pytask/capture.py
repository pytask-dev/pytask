"""Capture stdout and stderr during collection and execution.

References
----------

- <capture module in pytest
  <https://github.com/pytest-dev/pytest/blob/master/src/_pytest/capture.py>`
- <debugging module in pytest
  <https://github.com/pytest-dev/pytest/blob/master/src/_pytest/debugging.py>`

"""
import contextlib
import sys
from typing import Generator
from typing import Optional  # noqa: F401
from typing import TYPE_CHECKING
from typing import Union

import click
from _pytask.config import hookimpl
from _pytask.nodes import MetaTask
from _pytask.shared import get_first_non_none_value
from _pytest.capture import _colorama_workaround
from _pytest.capture import _get_multicapture
from _pytest.capture import _py36_windowsconsoleio_workaround
from _pytest.capture import _readline_workaround
from _pytest.capture import CaptureFixture  # noqa: F401
from _pytest.capture import CaptureResult
from _pytest.capture import MultiCapture  # noqa: F401

if TYPE_CHECKING:
    from typing_extensions import Literal

    _CaptureMethod = Literal["fd", "sys", "no", "tee-sys"]


@hookimpl
def pytask_extend_command_line_interface(cli):
    additional_parameters = [
        click.Option(
            ["--capture"],
            type=click.Choice(["fd", "no", "sys", "tee-sys"]),
            help="Per task capturing method.  [default: fd]",
        ),
        click.Option(["-s"], is_flag=True, help="Shortcut for --capture=no"),
    ]
    cli.commands["build"].params.extend(additional_parameters)


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
    capman.stop_global_capturing()
    capman.start_global_capturing()
    capman.suspend_global_capture()


def _capture_callback(x):
    if x in [None, "None", "none"]:
        x = None
    elif x in ["fd", "no", "sys", "tee-sys"]:
        pass
    else:
        raise ValueError("'capture' can only be one of ['fd', 'no', 'sys', 'tee-sys'].")


class CaptureManager:
    """The capture plugin.

    Manages that the appropriate capture method is enabled/disabled during collection
    and each test phase (setup, call, teardown). After each of those points, the
    captured output is obtained and attached to the collection/runtest report.

    There are two levels of capture:

    * global: enabled by default and can be suppressed by the ``-s`` option. This is
      always enabled/disabled during collection and each test phase.

    """

    def __init__(self, method: "_CaptureMethod") -> None:
        self._method = method
        self._global_capturing = None  # type: Optional[MultiCapture[str]]

    def __repr__(self) -> str:
        return ("<CaptureManager _method={!r} _global_capturing={!r} ").format(
            self._method, self._global_capturing
        )

    def is_capturing(self) -> Union[str, bool]:
        if self.is_globally_capturing():
            return "global"
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
        self.suspend_global_capture(in_)

    def resume(self) -> None:
        self.resume_global_capture()

    def read_global_capture(self) -> CaptureResult[str]:
        assert self._global_capturing is not None
        return self._global_capturing.readouterr()

    # Helper context managers

    @contextlib.contextmanager
    def global_and_fixture_disabled(self) -> Generator[None, None, None]:
        """Context manager to temporarily disable global capturing."""
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
    def task_capture(self, when: str, task: MetaTask) -> Generator[None, None, None]:
        self.resume_global_capture()
        self.activate_fixture()
        try:
            yield
        finally:
            self.deactivate_fixture()
            self.suspend_global_capture(in_=False)

        out, err = self.read_global_capture()
        task.add_report_section(when, "stdout", out)
        task.add_report_section(when, "stderr", err)

    # Hooks

    @hookimpl(hookwrapper=True)
    def pytask_execute_task_setup(self, task: MetaTask) -> Generator[None, None, None]:
        with self.task_capture("setup", task):
            yield

    @hookimpl(hookwrapper=True)
    def pytask_execute_task(self, task: MetaTask) -> Generator[None, None, None]:
        with self.task_capture("call", task):
            yield

    @hookimpl(hookwrapper=True)
    def pytask_execute_task_teardown(
        self, task: MetaTask
    ) -> Generator[None, None, None]:
        with self.task_capture("teardown", task):
            yield
