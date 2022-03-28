"""This module contains code related to click."""
from __future__ import annotations

from typing import Any

import click
from _pytask import __version__ as version
from _pytask.console import console
from click_default_group import DefaultGroup
from rich.highlighter import RegexHighlighter
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


_SWITCH_REGEX = r"(?P<switch>\-\w)\b"
_OPTION_REGEX = r"(?P<option>\-\-[\w\-]+)"
_METAVAR_REGEX = r"\-\-[\w\-]+(?P<metavar>[ |=][\w\.:]+)"


class OptionHighlighter(RegexHighlighter):
    """A highlighter for help texts."""

    highlights = [_SWITCH_REGEX, _OPTION_REGEX, _METAVAR_REGEX]


class ColoredGroup(DefaultGroup):
    """A subclass which colors groups with default commands."""

    def format_help(self: DefaultGroup, ctx: Any, formatter: Any) -> None:  # noqa: U100
        """Format the help text."""
        highlighter = OptionHighlighter()

        console.print(
            f"[b]pytask[/b] [dim]v{version}[/]\n", justify="center", highlight=False
        )

        console.print(
            "Usage: [b]pytask[/b] [b][OPTIONS][/b] [b][COMMAND][/b] [b][PATHS][/b]\n"
        )

        console.print(self.help, style="dim")
        console.print()

        commands_table = Table(highlight=True, box=None, show_header=False)

        for command_name in sorted(self.commands):
            command = self.commands[command_name]

            if command_name == self.default_cmd_name:
                formatted_name = Text(command_name + " *", style="command")
            else:
                formatted_name = Text(command_name, style="command")

            commands_table.add_row(formatted_name, highlighter(command.help))

        console.print(
            Panel(
                commands_table,
                title="[bold #ffffff]Commands[/bold #ffffff]",
                title_align="left",
                border_style="grey37",
            )
        )

        print_options(self, ctx)

        console.print(
            "[bold red]♥[/bold red] [white]https://pytask-dev.readthedocs.io[/]",
            justify="right",
        )


class ColoredCommand(click.Command):
    """Override Clicks help with a Richer version."""

    def format_help(
        self: click.Command, ctx: Any, formatter: Any  # noqa: U100
    ) -> None:
        """Format the help text."""
        console.print(
            f"[b]pytask[/b] [dim]v{version}[/]\n", justify="center", highlight=False
        )

        console.print(
            f"Usage: [b]pytask[/b] [b]{self.name}[/b] [b][OPTIONS][/b] [b][PATHS][/b]\n"
        )

        console.print(self.help, style="dim")
        console.print()

        print_options(self, ctx)

        console.print(
            "[bold red]♥[/bold red] [white]https://pytask-dev.readthedocs.io[/]",
            justify="right",
        )


def print_options(group_or_command: click.Command | DefaultGroup, ctx: Any) -> None:
    """Print options formatted with a table in a panel."""
    highlighter = OptionHighlighter()

    options_table = Table(highlight=True, box=None, show_header=False)

    for param in group_or_command.get_params(ctx):

        if isinstance(param, click.Argument):
            continue

        if getattr(param, "hidden", False):
            continue

        # The ordering of -h and --help is not fixed.
        if param.name == "help":
            opt1 = highlighter("-h")
            opt2 = highlighter("--help")
        elif len(param.opts) == 2:
            opt1 = highlighter(param.opts[0])
            opt2 = highlighter(param.opts[1])
        elif len(param.opts) == 1 and len(param.secondary_opts) == 1:
            opt1 = Text("")
            opt2 = highlighter(param.opts[0] + "/" + param.secondary_opts[0])
        else:
            opt1 = Text("")
            opt2 = highlighter(param.opts[0])

        if param.metavar:
            opt2 += Text(f" {param.metavar}", style="metavar")
        elif isinstance(param.type, click.Choice):
            choices = "[" + "|".join(param.type.choices) + "]"
            opt2 += Text(f" {choices}", style="metavar", overflow="fold")

        help_record = param.get_help_record(ctx)
        if help_record is None:
            help_text = ""
        else:
            help_text = Text.from_markup(param.get_help_record(ctx)[-1], emoji=False)

        options_table.add_row(opt1, opt2, highlighter(help_text))

    console.print(
        Panel(
            options_table,
            title="[bold #ffffff]Options[/bold #ffffff]",
            title_align="left",
            border_style="grey37",
        )
    )
