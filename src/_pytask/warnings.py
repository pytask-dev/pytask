"""Contains code for capturing warnings."""
from __future__ import annotations

from collections import defaultdict
from typing import Any
from typing import Generator
from typing import TYPE_CHECKING

import click
from _pytask.config import hookimpl
from _pytask.console import console
from _pytask.warnings_utils import catch_warnings_for_item
from _pytask.warnings_utils import parse_filterwarnings
from _pytask.warnings_utils import WarningReport
from attrs import define
from rich.padding import Padding
from rich.panel import Panel

if TYPE_CHECKING:
    from rich.console import Console
    from _pytask.node_protocols import PTask
    from rich.console import ConsoleOptions
    from _pytask.session import Session
    from rich.console import RenderResult


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
        session: Session, task: PTask
    ) -> Generator[None, None, None]:
        """Catch warnings while executing a task."""
        with catch_warnings_for_item(session=session, task=task):
            yield

    @staticmethod
    @hookimpl(trylast=True)
    def pytask_log_session_footer(session: Session) -> None:
        """Log warnings at the end of a session."""
        if session.warnings:
            renderable = _WarningsRenderable(session.warnings)
            panel = Panel(renderable, title="Warnings", style="warning")
            console.print(panel)


@define
class _WarningsRenderable:
    """A renderable for warnings."""

    warnings: list[WarningReport]
    max_locations: int = 5

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Group, sort, and display warnings."""
        msg_to_loc = defaultdict(list)
        for warning in self.warnings:
            location = warning.id_ or "{}:{}".format(*warning.fs_location)
            msg_to_loc[warning.message].append(location)
        message_to_locations = {k: sorted(v) for k, v in msg_to_loc.items()}

        reduced_message_to_locations = {}
        for message, locations in message_to_locations.items():
            if len(locations) > self.max_locations:
                adjusted_locations = locations[: self.max_locations]
                n_more_locations = len(locations[self.max_locations :])
                adjusted_locations.append(f"... in {n_more_locations} more locations.")
            else:
                adjusted_locations = locations
            reduced_message_to_locations[message] = adjusted_locations

        for message, locations in reduced_message_to_locations.items():
            yield from locations
            yield Padding.indent(message, 4)
        yield (
            "[bold red]♥[/bold red] "
            "https://pytask-dev.rtfd.io/en/stable/how_to_guides/capture_warnings.html"
        )
