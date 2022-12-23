"""This module contains code for capturing warnings."""
from __future__ import annotations

from collections import defaultdict
from typing import Any
from typing import Dict
from typing import Generator
from typing import List

import attr
import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.nodes import Task
from _pytask.session import Session
from _pytask.warnings_utils import catch_warnings_for_item
from _pytask.warnings_utils import parse_filterwarnings
from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.padding import Padding
from rich.panel import Panel


@hookimpl
def pytask_extend_command_line_interface(cli: click.Group) -> None:
    """Extend the cli."""
    cli.commands["build"].params.extend(
        [
            click.Option(
                ["--disable-warnings"],
                is_flag=True,
                default=False,
                help="Disables the summary for warnings.",
            )
        ]
    )


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    """Parse the configuration."""
    config["filterwarnings"] = parse_filterwarnings(config.get("filterwarnings"))
    config["markers"]["filterwarnings"] = "Add a filter for a warning to a task."


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Activate the warnings plugin if not disabled."""
    if not config["disable_warnings"]:
        config["pm"].register(WarningsNameSpace)


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
        self, console: Console, options: ConsoleOptions  # noqa: ARG002
    ) -> RenderResult:
        for message, locations in self.grouped_warnings.items():
            yield from locations
            yield Padding.indent(message, 4)
        yield (
            "[bold red]♥[/bold red] "
            + "https://pytask-dev.rtfd.io/en/stable/how_to_guides/capture_warnings.html"
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
