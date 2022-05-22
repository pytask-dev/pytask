"""This module contains code for capturing warnings."""
from __future__ import annotations

import functools
import re
import textwrap
import warnings
from collections import defaultdict
from contextlib import contextmanager
from typing import Any
from typing import cast
from typing import Dict
from typing import Generator
from typing import List

import attr
import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.mark_utils import get_marks
from _pytask.nodes import Task
from _pytask.outcomes import Exit
from _pytask.session import Session
from _pytask.warnings_utils import WarningReport
from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.padding import Padding
from rich.panel import Panel


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the cli."""
    cli.commands["build"].params.append(
        click.Option(
            ["--disable-warnings"],
            is_flag=True,
            default=False,
            help="Disables the summary for warnings.",
        )
    )


@hookimpl
def pytask_parse_config(
    config: dict[str, Any],
    config_from_file: dict[str, Any],
    config_from_cli: dict[str, Any],
) -> None:
    """Parse the configuration."""
    config["disable_warnings"] = config_from_cli.get("disable_warnings", False)
    config["filterwarnings"] = _parse_filterwarnings(
        config_from_file.get("filterwarnings")
    )
    config["markers"]["filterwarnings"] = "Add a filter for a warning to a task."


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Activate the warnings plugin if not disabled."""
    if not config["disable_warnings"]:
        config["pm"].register(WarningsNameSpace)


def _parse_filterwarnings(x: str | list[str] | None) -> list[str]:
    """Parse filterwarnings."""
    if x is None:
        return []
    elif isinstance(x, str):
        return [i.strip() for i in x.split("\n")]
    elif isinstance(x, list):
        return [i.strip() for i in x]
    else:
        raise TypeError("'filterwarnings' must be a str, list[str] or None.")


@contextmanager
def catch_warnings_for_item(
    session: Session,
    task: Task | None = None,
    when: str | None = None,
) -> Generator[None, None, None]:
    """Context manager that catches warnings generated in the contained execution block.
    ``item`` can be None if we are not in the context of an item execution.
    Each warning captured triggers the ``pytest_warning_recorded`` hook.
    """
    with warnings.catch_warnings(record=True) as log:
        # mypy can't infer that record=True means log is not None; help it.
        assert log is not None

        for arg in session.config["filterwarnings"]:
            warnings.filterwarnings(*parse_warning_filter(arg, escape=False))

        # apply filters from "filterwarnings" marks
        if task is not None:
            for mark in get_marks(task, "filterwarnings"):
                for arg in mark.args:
                    warnings.filterwarnings(*parse_warning_filter(arg, escape=False))

        yield

        if task is not None:
            id_ = task.short_name
        else:
            id_ = when

        for warning_message in log:
            fs_location = warning_message.filename, warning_message.lineno
            session.warnings.append(
                WarningReport(
                    message=warning_record_to_str(warning_message),
                    fs_location=fs_location,
                    id_=id_,
                )
            )


@functools.lru_cache(maxsize=50)
def parse_warning_filter(
    arg: str, *, escape: bool
) -> tuple[warnings._ActionKind, str, type[Warning], str, int]:
    """Parse a warnings filter string.

    This is copied from warnings._setoption with the following changes:

    - Does not apply the filter.
    - Escaping is optional.
    - Raises UsageError so we get nice error messages on failure.

    """
    __tracebackhide__ = True
    error_template = textwrap.dedent(
        f"""\
        while parsing the following warning configuration:
          {arg}
        This error occurred:
        {{error}}
        """
    )

    parts = arg.split(":")
    if len(parts) > 5:
        doc_url = (
            "https://docs.python.org/3/library/warnings.html#describing-warning-filters"
        )
        error = textwrap.dedent(
            f"""\
            Too many fields ({len(parts)}), expected at most 5 separated by colons:
              action:message:category:module:line
            For more information please consult: {doc_url}
            """
        )
        raise Exit(error_template.format(error=error))

    while len(parts) < 5:
        parts.append("")
    action_, message, category_, module, lineno_ = (s.strip() for s in parts)
    try:
        action: warnings._ActionKind = warnings._getaction(action_)  # type: ignore
    except warnings._OptionError as e:
        raise Exit(error_template.format(error=str(e)))
    try:
        category: type[Warning] = _resolve_warning_category(category_)
    except Exit as e:
        raise Exit(str(e))
    if message and escape:
        message = re.escape(message)
    if module and escape:
        module = re.escape(module) + r"\Z"
    if lineno_:
        try:
            lineno = int(lineno_)
            if lineno < 0:
                raise ValueError("number is negative")
        except ValueError as e:
            raise Exit(error_template.format(error=f"invalid lineno {lineno_!r}: {e}"))
    else:
        lineno = 0
    return action, message, category, module, lineno


def _resolve_warning_category(category: str) -> type[Warning]:
    """
    Copied from warnings._getcategory, but changed so it lets exceptions (specially
    ImportErrors) propagate so we can get access to their tracebacks (#9218).

    """
    __tracebackhide__ = True
    if not category:
        return Warning

    if "." not in category:
        import builtins as m

        klass = category
    else:
        module, _, klass = category.rpartition(".")
        m = __import__(module, None, None, [klass])
    cat = getattr(m, klass)
    if not issubclass(cat, Warning):
        raise Exception(f"{cat} is not a Warning subclass")
    return cast(type[Warning], cat)


def warning_record_to_str(warning_message: warnings.WarningMessage) -> str:
    """Convert a warnings.WarningMessage to a string."""
    msg = warnings.formatwarning(
        message=warning_message.message,
        category=warning_message.category,
        filename=warning_message.filename,
        lineno=warning_message.lineno,
        line=warning_message.line,
    )
    return msg


class WarningsNameSpace:
    """A namespace for the warnings plugin."""

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_collect(session: Session) -> Generator[None, None, None]:
        """Catch warnings while executing a task."""
        with catch_warnings_for_item(session=session):
            yield

    @staticmethod
    @hookimpl(hookwrapper=True)
    def pytask_execute_task(
        session: Session, task: Task
    ) -> Generator[None, None, None]:
        """Catch warnings while executing a task."""
        with catch_warnings_for_item(session=session, task=task):
            yield

    @staticmethod
    @hookimpl(trylast=True)
    def pytask_log_session_footer(session: Session) -> None:
        """Log warnings at the end of a session."""
        if session.warnings:
            grouped_warnings = defaultdict(list)
            for warning in session.warnings:
                location = (
                    warning.id_
                    if warning.id_ is not None
                    else "{}:{}".format(*warning.fs_location)
                )
                grouped_warnings[warning.message].append(location)
            sorted_gw = {k: sorted(v) for k, v in grouped_warnings.items()}

            reduced_gw = _reduce_grouped_warnings(sorted_gw)

            renderable = MyRenderable(reduced_gw)

            panel = Panel(renderable, title="Warnings", style="warning")
            console.print(panel)


@attr.s
class MyRenderable:
    """A renderable for warnings."""

    grouped_warnings = attr.ib(type=Dict[str, List[str]])

    def __rich_console__(
        self, console: Console, options: ConsoleOptions  # noqa: U100
    ) -> RenderResult:
        for message, locations in self.grouped_warnings.items():
            yield from locations
            yield Padding.indent(message, 4)
        yield (
            "[bold red]♥[/bold red] "
            + "https://pytask-dev.rtdf.io/en/stable/how_to_guides/capture_warnings.html"
        )


def _reduce_grouped_warnings(
    grouped_warnings: dict[str, list[str]], max_locations: int = 5
) -> dict[str, list[str]]:
    """Reduce grouped warnings."""
    reduced_gw = {}
    for message, locations in grouped_warnings.items():
        if len(locations) > max_locations:
            adjusted_locations = locations[:max_locations]
            n_more_locations = len(locations[max_locations:])
            adjusted_locations.append(f"... in {n_more_locations} more locations.")
        else:
            adjusted_locations = locations
        reduced_gw[message] = adjusted_locations
    return reduced_gw
