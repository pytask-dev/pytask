"""Add general logging capabilities."""

from __future__ import annotations

import contextlib
import io
import logging
import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import NamedTuple

import click
import pluggy
from rich.text import Text

import _pytask
from _pytask.capture_utils import ShowCapture
from _pytask.console import console
from _pytask.pluginmanager import hookimpl
from _pytask.reports import ExecutionReport
from _pytask.shared import convert_to_enum
from _pytask.traceback import Traceback

if TYPE_CHECKING:
    from collections.abc import Generator

    from pluggy._manager import DistFacade

    from _pytask.capture import CaptureManager
    from _pytask.live import LiveManager
    from _pytask.node_protocols import PTask
    from _pytask.outcomes import CollectionOutcome
    from _pytask.outcomes import TaskOutcome
    from _pytask.session import Session


with contextlib.suppress(ImportError):
    pass


if TYPE_CHECKING:
    LoggingStreamHandler = logging.StreamHandler[io.StringIO]
else:
    LoggingStreamHandler = logging.StreamHandler


DEFAULT_LOG_FORMAT = "%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"


class _TimeUnit(NamedTuple):
    singular: str
    plural: str
    short: str
    in_seconds: int


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    cli.commands["build"].params.extend(
        [
            click.Option(
                ["--log-cli/--no-log-cli"],
                default=False,
                help="Enable live log display during task execution.",
            ),
            click.Option(
                ["--log-cli-level"],
                default=None,
                metavar="LEVEL",
                help="CLI logging level.",
            ),
            click.Option(
                ["--log-cli-format"],
                default=None,
                help="Log format used by the logging module for live logs.",
            ),
            click.Option(
                ["--log-cli-date-format"],
                default=None,
                help="Log date format used by the logging module for live logs.",
            ),
            click.Option(
                ["--show-locals"],
                is_flag=True,
                default=False,
                help="Show local variables in tracebacks.",
            ),
            click.Option(
                ["--log-level"],
                default=None,
                metavar="LEVEL",
                help=(
                    "Level of messages to catch/display. Not set by default, so it "
                    "depends on the logger configuration."
                ),
            ),
            click.Option(
                ["--log-format"],
                default=DEFAULT_LOG_FORMAT,
                help="Log format used by the logging module.",
            ),
            click.Option(
                ["--log-date-format"],
                default=DEFAULT_LOG_DATE_FORMAT,
                help="Log date format used by the logging module.",
            ),
            click.Option(
                ["--log-file"],
                default=None,
                help="Path to a file where logging will be written.",
            ),
            click.Option(
                ["--log-file-mode"],
                default="w",
                type=click.Choice(["w", "a"]),
                help="Log file open mode.",
            ),
            click.Option(
                ["--log-file-level"],
                default=None,
                metavar="LEVEL",
                help="Log file logging level.",
            ),
            click.Option(
                ["--log-file-format"],
                default=None,
                help="Log format used by the logging module for the log file.",
            ),
            click.Option(
                ["--log-file-date-format"],
                default=None,
                help="Log date format used by the logging module for the log file.",
            ),
        ]
    )


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    config["show_capture"] = convert_to_enum(config["show_capture"], ShowCapture)
    config["log_cli_level"] = _parse_log_level(
        config["log_cli_level"], option_name="log_cli_level"
    )
    config["log_level"] = _parse_log_level(config["log_level"], option_name="log_level")
    config["log_file_level"] = _parse_log_level(
        config["log_file_level"], option_name="log_file_level"
    )

    log_file = config["log_file"]
    if log_file is None:
        return

    log_file = Path(log_file)
    if not log_file.is_absolute():
        log_file = config["root"].joinpath(log_file)
    config["log_file"] = log_file.resolve()


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    # Set class variables on traceback object.
    Traceback._show_locals = config["show_locals"]
    # Set class variables on Executionreport.
    ExecutionReport.editor_url_scheme = config["editor_url_scheme"]
    ExecutionReport.show_capture = config["show_capture"]
    ExecutionReport.show_locals = config["show_locals"]

    config["pm"].register(LoggingManager.from_config(config), "loggingmanager")


@hookimpl
def pytask_log_session_header(session: Session) -> None:
    """Log the header of a pytask session."""
    console.rule("Start pytask session", style="default")
    console.print(
        f"Platform: {sys.platform} -- Python {platform.python_version()}, "
        f"pytask {_pytask.__version__}, pluggy {pluggy.__version__}",
        highlight=False,
        soft_wrap=True,
    )
    console.print(f"Root: {session.config['root']}")
    if session.config["config"] is not None:
        console.print(f"Configuration: {session.config['config']}")

    plugin_info = session.config["pm"].list_plugin_distinfo()
    if plugin_info:
        formatted_plugins_w_versions = ", ".join(
            _format_plugin_names_and_versions(plugin_info)
        )
        console.print(f"Plugins: {formatted_plugins_w_versions}")


def _format_plugin_names_and_versions(
    plugininfo: list[tuple[str, DistFacade]],
) -> list[str]:
    """Format name and version of loaded plugins."""
    values: list[str] = []
    for _, dist in plugininfo:
        # Gets us name and version!
        name = f"{dist.project_name}-{dist.version}"
        # Questionable convenience, but it keeps things short.
        name = name.removeprefix("pytask-")
        # We decided to print python package names they can have more than one plugin.
        if name not in values:
            values.append(name)
    return values


@hookimpl
def pytask_log_session_footer(
    duration: float,
    outcome: CollectionOutcome | TaskOutcome,
) -> None:
    """Format the footer of the log message."""
    formatted_duration = _format_duration(duration)
    message = Text(
        f"{outcome.description} in {formatted_duration}", style=outcome.style
    )
    console.rule(message, style=outcome.style)


@hookimpl
def pytask_unconfigure() -> None:
    """Reset class variables."""
    Traceback._show_locals = False
    ExecutionReport.editor_url_scheme = "file"
    ExecutionReport.show_capture = ShowCapture.ALL
    ExecutionReport.show_locals = False


_TIME_UNITS: list[_TimeUnit] = [
    _TimeUnit(singular="day", plural="days", short="d", in_seconds=86400),
    _TimeUnit(singular="hour", plural="hours", short="h", in_seconds=3600),
    _TimeUnit(singular="minute", plural="minutes", short="m", in_seconds=60),
    _TimeUnit(singular="second", plural="seconds", short="s", in_seconds=1),
]


def _format_duration(duration: float) -> str:
    """Format the duration."""
    duration_tuples = _humanize_time(duration, "seconds", short_label=False)

    # Remove seconds if the execution lasted days or hours.
    if duration_tuples[0][1] in ("day", "days", "hour", "hours"):
        duration_tuples = [
            i for i in duration_tuples if i[1] not in ("second", "seconds")
        ]

    return ", ".join([" ".join(str(x) for x in i) for i in duration_tuples])


def _humanize_time(  # noqa: C901, PLR0912
    amount: float, unit: str, short_label: bool = False
) -> list[tuple[float, str]]:
    """Humanize the time.

    Examples
    --------
    >>> _humanize_time(173, "hours")
    [(7, 'days'), (5, 'hours')]
    >>> _humanize_time(173.345, "seconds")
    [(2, 'minutes'), (53.34, 'seconds')]
    >>> _humanize_time(173, "hours", short_label=True)
    [(7, 'd'), (5, 'h')]
    >>> _humanize_time(0, "seconds", short_label=True)
    [(0, 's')]
    >>> _humanize_time(1, "unknown_unit")
    Traceback (most recent call last):
    ...
    ValueError: The time unit 'unknown_unit' is not known.

    """
    index = None
    for i, time_unit in enumerate(_TIME_UNITS):
        if unit in (time_unit.singular, time_unit.plural):
            index = i
            break
    else:
        msg = f"The time unit {unit!r} is not known."
        raise ValueError(msg)

    seconds = amount * _TIME_UNITS[index].in_seconds
    result: list[tuple[float, str]] = []
    remaining_seconds = seconds

    for time_unit in _TIME_UNITS:
        whole_units = int(remaining_seconds / time_unit.in_seconds)

        if time_unit.singular == "second" and remaining_seconds:
            last_seconds = round(remaining_seconds, 2)
            if short_label:
                label = time_unit.short
            elif last_seconds == 1:
                label = time_unit.singular
            else:
                label = time_unit.plural
            result.append((last_seconds, label))

        elif whole_units >= 1 and time_unit.singular != "seconds":
            if short_label:
                label = time_unit.short
            elif whole_units == 1:
                label = time_unit.singular
            else:
                label = time_unit.plural

            result.append((whole_units, label))
            remaining_seconds -= whole_units * time_unit.in_seconds

    if not result:
        result.append(
            (0, _TIME_UNITS[-1].short if short_label else _TIME_UNITS[-1].plural)
        )

    return result


class LogCaptureHandler(LoggingStreamHandler):
    """Capture logs in a string buffer."""

    def __init__(self) -> None:
        super().__init__(io.StringIO())

    def reset(self) -> None:
        old_stream = self.setStream(io.StringIO())
        if old_stream is not None:
            old_stream.close()

    def get_text(self) -> str:
        return self.stream.getvalue().strip()


class LiveLogHandler(logging.Handler):
    """Write log records to the terminal immediately."""

    def __init__(
        self,
        *,
        plugin_manager: Any,
    ) -> None:
        super().__init__()
        self.plugin_manager = plugin_manager

    def _get_capture_manager(self) -> CaptureManager | None:
        capture_manager = self.plugin_manager.get_plugin("capturemanager")
        return capture_manager if hasattr(capture_manager, "write_to_stdout") else None

    def _get_live_manager(self) -> LiveManager | None:
        live_manager = self.plugin_manager.get_plugin("live_manager")
        return live_manager if hasattr(live_manager, "pause") else None

    def emit(self, record: logging.LogRecord) -> None:
        message = self.format(record)
        capture_manager = self._get_capture_manager()
        live_manager = self._get_live_manager()
        resume_live = live_manager is not None and live_manager.is_started

        if resume_live and live_manager is not None:
            live_manager.pause()

        try:
            if capture_manager is not None:
                capture_manager.write_to_stdout(message + "\n")
            else:
                sys.stdout.write(message + "\n")
                sys.stdout.flush()
        finally:
            if resume_live and live_manager is not None:
                live_manager.resume()


class LoggingManager:
    """Capture task logs for reports and optional log files.

    This intentionally follows pytest's handler-on-root design instead of trying to
    intercept logging internals. The tradeoff is that task-local logging
    reconfiguration is not fully isolated from pytask:

    - ``logging.basicConfig()`` inside a task can become a no-op because pytask has
      already attached a handler to the root logger.
    - ``logging.basicConfig(force=True)`` or direct mutation of ``root.handlers`` can
      remove or close pytask-managed handlers for the remainder of the task/session.

    We accept these limitations for parity with pytest and to keep the integration
    simple. A more isolated design would need to avoid attaching handlers to the root
    logger in the first place.
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        formatter: logging.Formatter,
        live_log_handler: logging.Handler | None,
        log_cli_level: int | None,
        log_level: int | None,
        log_file_handler: logging.FileHandler | None,
        log_file_level: int | None,
    ) -> None:
        self.live_log_handler = live_log_handler
        self.log_cli_level = log_cli_level
        self.log_level = log_level
        self.log_file_level = log_file_level
        self.report_handler = LogCaptureHandler()
        self.report_handler.setFormatter(formatter)
        self.log_file_handler = log_file_handler

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> LoggingManager:
        log_cli_level = (
            config["log_cli_level"]
            if config["log_cli_level"] is not None
            else config["log_level"]
        )
        log_file_level = (
            config["log_file_level"]
            if config["log_file_level"] is not None
            else config["log_level"]
        )
        live_log_handler = _create_live_log_handler(
            config=config,
            log_cli_level=log_cli_level,
        )
        log_file_handler = _create_log_file_handler(
            log_file=config["log_file"],
            log_file_format=config["log_file_format"] or config["log_format"],
            log_file_date_format=config["log_file_date_format"]
            or config["log_date_format"],
            log_file_level=log_file_level,
            log_file_mode=config["log_file_mode"],
        )
        return cls(
            formatter=logging.Formatter(
                config["log_format"], datefmt=config["log_date_format"]
            ),
            live_log_handler=live_log_handler,
            log_cli_level=log_cli_level if live_log_handler is not None else None,
            log_level=config["log_level"],
            log_file_handler=log_file_handler,
            log_file_level=log_file_level if log_file_handler is not None else None,
        )

    @contextlib.contextmanager
    def _catching_logs(self) -> Generator[None, None, None]:
        root_logger = logging.getLogger()
        handlers: list[logging.Handler] = [self.report_handler]
        if self.live_log_handler is not None:
            handlers.append(self.live_log_handler)
        if self.log_file_handler is not None:
            handlers.append(self.log_file_handler)

        original_level = root_logger.level
        report_level = self.log_level if self.log_level is not None else original_level
        configured_levels = [
            level
            for level in (
                report_level,
                self.log_cli_level,
                self.log_file_level,
            )
            if level not in (None, logging.NOTSET)
        ]

        try:
            # Attaching handlers to the root logger is the key design choice here. It
            # keeps pytask aligned with pytest, but it also means task code that
            # reconfigures the root logger can affect pytask's own logging handlers.
            for handler in handlers:
                handler.setLevel(
                    report_level if handler is self.report_handler else handler.level
                )
                root_logger.addHandler(handler)

            if configured_levels:
                root_logger.setLevel(min(original_level, *configured_levels))
            yield
        finally:
            for handler in reversed(handlers):
                root_logger.removeHandler(handler)
            root_logger.setLevel(original_level)

    @contextlib.contextmanager
    def _task_logging(self, when: str, task: PTask) -> Generator[None, None, None]:
        self.report_handler.reset()
        with self._catching_logs():
            try:
                yield
            finally:
                log = self.report_handler.get_text()
                if log:
                    task.report_sections.append((when, "log", log))

    @hookimpl(wrapper=True)
    def pytask_execute_task_setup(self, task: PTask) -> Generator[None, None, None]:
        with self._task_logging("setup", task):
            return (yield)

    @hookimpl(wrapper=True)
    def pytask_execute_task(self, task: PTask) -> Generator[None, None, None]:
        with self._task_logging("call", task):
            return (yield)

    @hookimpl(wrapper=True)
    def pytask_execute_task_teardown(self, task: PTask) -> Generator[None, None, None]:
        with self._task_logging("teardown", task):
            return (yield)

    @hookimpl
    def pytask_unconfigure(self) -> None:
        if self.log_file_handler is not None:
            self.log_file_handler.close()


def _parse_log_level(value: Any, *, option_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        msg = f"{option_name!r} must be an int, str, or None, not {type(value)!r}."
        raise click.BadParameter(msg)

    normalized_value = value.upper()
    level = getattr(logging, normalized_value, None)
    if not isinstance(level, int):
        msg = f"{value!r} is not recognized as a logging level name."
        raise click.BadParameter(msg)
    return level


def _create_log_file_handler(
    *,
    log_file: Path | None,
    log_file_date_format: str,
    log_file_format: str,
    log_file_level: int | None,
    log_file_mode: str,
) -> logging.FileHandler | None:
    if log_file is None:
        return None

    log_file.parent.mkdir(parents=True, exist_ok=True)
    # This handler is session-scoped and reattached around each task. If user code
    # force-reconfigures the root logger, Python may close this handler as part of
    # removing existing root handlers.
    log_file_handler = logging.FileHandler(
        log_file, mode=log_file_mode, encoding="utf-8"
    )
    log_file_handler.setFormatter(
        logging.Formatter(log_file_format, datefmt=log_file_date_format)
    )
    log_file_handler.setLevel(
        log_file_level if log_file_level is not None else logging.NOTSET
    )
    return log_file_handler


def _create_live_log_handler(
    *, config: dict[str, Any], log_cli_level: int | None
) -> logging.Handler | None:
    if not config["log_cli"]:
        return None

    live_log_handler = LiveLogHandler(plugin_manager=config["pm"])
    live_log_handler.setFormatter(
        logging.Formatter(
            config["log_cli_format"] or config["log_format"],
            datefmt=config["log_cli_date_format"] or config["log_date_format"],
        )
    )
    live_log_handler.setLevel(
        log_cli_level if log_cli_level is not None else logging.NOTSET
    )
    return live_log_handler
