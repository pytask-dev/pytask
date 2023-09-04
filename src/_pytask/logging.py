"""Add general logging capabilities."""
from __future__ import annotations

import contextlib
import platform
import sys
import warnings
from typing import Any
from typing import NamedTuple
from typing import TYPE_CHECKING

import _pytask
import click
import pluggy
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import IS_WINDOWS_TERMINAL
from rich.text import Text

if TYPE_CHECKING:
    from pluggy._manager import DistFacade
    from _pytask.outcomes import TaskOutcome
    from _pytask.session import Session
    from _pytask.outcomes import CollectionOutcome


with contextlib.suppress(ImportError):
    pass


class _TimeUnit(NamedTuple):
    singular: str
    plural: str
    short: str
    in_seconds: int


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    show_locals_option = click.Option(
        ["--show-locals"],
        is_flag=True,
        default=False,
        help="Show local variables in tracebacks.",
    )
    cli.commands["build"].params.append(show_locals_option)


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse configuration."""
    if config["editor_url_scheme"] not in ("no_link", "file") and IS_WINDOWS_TERMINAL:
        config["editor_url_scheme"] = "file"
        warnings.warn(
            "Windows Terminal does not support url schemes to applications, yet."
            "See https://github.com/pytask-dev/pytask/issues/171 for more information. "
            "Resort to `editor_url_scheme='file'`.",
            stacklevel=1,
        )


@hookimpl
def pytask_log_session_header(session: Session) -> None:
    """Log the header of a pytask session."""
    console.rule("Start pytask session", style=None)
    console.print(
        f"Platform: {sys.platform} -- Python {platform.python_version()}, "
        f"pytask {_pytask.__version__}, pluggy {pluggy.__version__}"
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
    plugininfo: list[tuple[str, DistFacade]]
) -> list[str]:
    """Format name and version of loaded plugins."""
    values: list[str] = []
    for _, dist in plugininfo:
        # Gets us name and version!
        name = f"{dist.project_name}-{dist.version}"
        # Questionable convenience, but it keeps things short.
        if name.startswith("pytask-"):
            name = name[7:]
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

    return ", ".join([" ".join(map(str, i)) for i in duration_tuples])


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
