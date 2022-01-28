"""Add general logging capabilities."""
import platform
import sys
import warnings
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

import _pytask
import click
import pluggy
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.console import IS_WINDOWS_TERMINAL
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from _pytask.session import Session
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from rich.text import Text


try:
    from pluggy._manager import DistFacade
except ImportError:
    from pluggy.manager import DistFacade


if TYPE_CHECKING and sys.version_info >= (3, 8):
    from typing import TypedDict

    class _TimeUnit(TypedDict):
        singular: str
        plural: str
        short: str
        in_seconds: int

    if sys.version_info >= (3, 8):
        from typing import Literal
    else:
        from typing_extensions import Literal

    _ShowTraceback = Literal["no", "yes"]


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    show_locals_option = click.Option(
        ["--show-locals"],
        is_flag=True,
        default=None,
        help="Show local variables in tracebacks.",
    )
    cli.commands["build"].params.append(show_locals_option)


@hookimpl
def pytask_parse_config(
    config: Dict[str, Any],
    config_from_file: Dict[str, Any],
    config_from_cli: Dict[str, Any],
) -> None:
    """Parse configuration."""
    config["show_locals"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="show_locals",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )
    config["editor_url_scheme"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="editor_url_scheme",
        default="file",
        callback=lambda x: None if x in [None, "none", "None"] else str(x),
    )
    if config["editor_url_scheme"] not in ["no_link", "file"] and IS_WINDOWS_TERMINAL:
        config["editor_url_scheme"] = "file"
        warnings.warn(
            "Windows Terminal does not support url schemes to applications, yet."
            "See https://github.com/pytask-dev/pytask/issues/171 for more information. "
            "Resort to `editor_url_scheme='file'`."
        )
    config["show_traceback"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="show_traceback",
        default="yes",
        callback=_show_traceback_callback,
    )


def _show_traceback_callback(
    x: Optional["_ShowTraceback"],
) -> Optional["_ShowTraceback"]:
    """Validate the passed options for showing tracebacks."""
    if x in [None, "None", "none"]:
        x = None
    elif x in ["no", "yes"]:
        pass
    else:
        raise ValueError("'show_traceback' can only be one of ['no', 'yes'].")
    return x


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
    plugininfo: List[Tuple[str, DistFacade]]
) -> List[str]:
    """Format name and version of loaded plugins."""
    values: List[str] = []
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
    outcome: Union[CollectionOutcome, TaskOutcome],
) -> None:
    """Format the footer of the log message."""
    formatted_duration = _format_duration(duration)
    message = Text(
        f"{outcome.description} in {formatted_duration}", style=outcome.style
    )
    console.rule(message, style=outcome.style)


_TIME_UNITS: List["_TimeUnit"] = [
    {"singular": "day", "plural": "days", "short": "d", "in_seconds": 86400},
    {"singular": "hour", "plural": "hours", "short": "h", "in_seconds": 3600},
    {"singular": "minute", "plural": "minutes", "short": "m", "in_seconds": 60},
    {"singular": "second", "plural": "seconds", "short": "s", "in_seconds": 1},
]


def _format_duration(duration: float) -> str:
    """Format the duration."""
    duration_tuples = _humanize_time(duration, "seconds", short_label=False)

    # Remove seconds if the execution lasted days or hours.
    if duration_tuples[0][1] in ["day", "days", "hour", "hours"]:
        duration_tuples = [
            i for i in duration_tuples if i[1] not in ["second", "seconds"]
        ]

    formatted_duration = ", ".join([" ".join(map(str, i)) for i in duration_tuples])
    return formatted_duration


def _humanize_time(
    amount: Union[int, float], unit: str, short_label: bool = False
) -> List[Tuple[float, str]]:
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
    for i, entry in enumerate(_TIME_UNITS):
        if unit in [entry["singular"], entry["plural"]]:
            index = i
            break
    else:
        raise ValueError(f"The time unit {unit!r} is not known.")

    seconds = amount * _TIME_UNITS[index]["in_seconds"]
    result: List[Tuple[float, str]] = []
    remaining_seconds = seconds
    for entry in _TIME_UNITS:
        whole_units = int(remaining_seconds / entry["in_seconds"])

        if entry["singular"] == "second" and remaining_seconds:
            last_seconds = round(remaining_seconds, 2)
            if short_label:
                label = entry["short"]
            elif last_seconds == 1:
                label = entry["singular"]
            else:
                label = entry["plural"]
            result.append((last_seconds, label))

        elif whole_units >= 1:
            if entry["singular"] != "seconds":
                if short_label:
                    label = entry["short"]
                elif whole_units == 1:
                    label = entry["singular"]
                else:
                    label = entry["plural"]

                result.append((whole_units, label))
                remaining_seconds -= whole_units * entry["in_seconds"]

    if not result:
        result.append(
            (0, _TIME_UNITS[-1]["short"] if short_label else _TIME_UNITS[-1]["plural"])
        )

    return result
