"""Generate CLI command reference tables for docs."""

from __future__ import annotations

import enum
import re
from pathlib import Path

import click

from _pytask.cli import cli

OUT_DIR = Path("docs/source/_static/md/commands")
COMMANDS = ("build", "clean", "collect", "dag", "markers", "profile")


def _strip_click_suffixes(help_text: str) -> str:
    """Remove click-appended suffixes like default/range metadata."""
    help_text = re.sub(r"\s*\[default: .*?\]\s*$", "", help_text)
    help_text = re.sub(r"\s*\[[0-9<>=,\.\-A-Za-z]+\]\s*$", "", help_text)
    return help_text.strip()


def _format_default(option: click.Option) -> str:
    default = option.default
    result = "-"

    if isinstance(default, bool):
        if option.secondary_opts:
            active = option.opts[0] if default else option.secondary_opts[0]
            result = f"`{active}`"
        else:
            result = f"`{str(default).lower()}`"
    elif default is None or (isinstance(default, tuple | list) and not default):
        result = "-"
    elif isinstance(default, enum.Enum):
        if str(default.value).startswith("<object object at"):
            result = "-"
        else:
            result = f"`{default.value}`"
    elif default == float("inf"):
        result = "`inf`"
    else:
        text = str(default)
        result = "-" if text.startswith("<object object at") else f"`{text}`"

    return result


def _command_context(command_name: str) -> click.Context:
    command = cli.commands[command_name]
    return click.Context(command, info_name=f"pytask {command_name}")


def _write_options(command_name: str) -> None:
    command = cli.commands[command_name]
    ctx = _command_context(command_name)

    lines = ["| Option | Default | Description |", "|---|---|---|"]

    for param in command.params:
        if not isinstance(param, click.Option):
            continue

        help_record = param.get_help_record(ctx)
        if help_record is None:
            continue

        option_decl, description = help_record
        lines.append(
            "| "
            f"`{option_decl}`"
            " | "
            f"{_format_default(param)}"
            " | "
            f"{_strip_click_suffixes(description)}"
            " |"
        )

    lines.append("| `-h, --help` | - | Show this message and exit. |")

    output = "\n".join(lines) + "\n"
    OUT_DIR.joinpath(f"{command_name}-options.md").write_text(output)


def _write_arguments(command_name: str) -> None:
    command = cli.commands[command_name]

    lines = ["| Argument | Description |", "|---|---|"]
    has_arguments = False

    for param in command.params:
        if not isinstance(param, click.Argument):
            continue

        has_arguments = True
        metavar = param.make_metavar(click.Context(command)).strip()
        description = "Paths where pytask looks for task files and configuration."
        lines.append(f"| `{metavar}` | {description} |")

    if not has_arguments:
        lines.append("| - | This command does not take positional arguments. |")

    output = "\n".join(lines) + "\n"
    OUT_DIR.joinpath(f"{command_name}-arguments.md").write_text(output)


def _write_commands_table() -> None:
    lines = ["| Command | Description |", "|---|---|"]
    lines.extend(
        f"| [`{name}`]({name}.md) | {cli.commands[name].help} |" for name in COMMANDS
    )

    output = "\n".join(lines) + "\n"
    OUT_DIR.joinpath("command-list.md").write_text(output)


def _write_root_options() -> None:
    ctx = click.Context(cli, info_name="pytask")
    lines = ["| Option | Description |", "|---|---|"]

    for param in cli.params:
        if not isinstance(param, click.Option):
            continue
        help_record = param.get_help_record(ctx)
        if help_record is None:
            continue
        option_decl, description = help_record
        lines.append(f"| `{option_decl}` | {_strip_click_suffixes(description)} |")

    lines.append("| `-h, --help` | Show this message and exit. |")

    output = "\n".join(lines) + "\n"
    OUT_DIR.joinpath("root-options.md").write_text(output)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for command_name in COMMANDS:
        _write_arguments(command_name)
        _write_options(command_name)

    _write_commands_table()
    _write_root_options()


if __name__ == "__main__":
    main()
