"""Generate a one-page CLI reference for the documentation."""

from __future__ import annotations

import argparse
import enum
import html
import inspect
import re
import sys
from pathlib import Path

import click

from _pytask.cli import cli

OUT_PATH = Path("docs/source/reference_guides/commands.md")


def _strip_click_suffixes(help_text: str) -> str:
    """Remove click-appended suffixes like default or range metadata."""
    help_text = re.sub(r"\s*\[default: .*?\]\s*$", "", help_text)
    help_text = re.sub(r"\s*\[[0-9<>=,\.\-A-Za-z]+\]\s*$", "", help_text)
    return help_text.strip()


def _format_default(option: click.Option) -> str | None:
    result: str | None = None

    if not option.expose_value:
        return None

    default = option.default

    if isinstance(default, bool):
        if option.secondary_opts:
            result = option.opts[0] if default else option.secondary_opts[0]
        else:
            result = str(default).lower()
    elif default is None or (isinstance(default, tuple | list) and not default):
        result = None
    elif isinstance(default, enum.Enum):
        value = str(default.value)
        result = None if value.startswith("<object object at") else value
    elif default == float("inf"):
        result = "inf"
    else:
        text = str(default)
        result = None if text.startswith("<object object at") else text

    return result


def _command_description(command: click.Command) -> str:
    help_text = command.help or command.short_help or ""
    return inspect.cleandoc(help_text).strip()


def _command_anchor(parts: tuple[str, ...]) -> str:
    return "-".join(parts)


def _option_anchor(parts: tuple[str, ...], option: click.Option) -> str:
    if option.opts:
        names = [opt for opt in option.opts if opt.startswith("--")]
        candidate = names[0] if names else option.opts[0]
        suffix = candidate.lstrip("-")
    else:
        suffix = option.name or "option"
    return f"{_command_anchor(parts)}--{suffix}"


def _argument_anchor(parts: tuple[str, ...], argument: click.Argument) -> str:
    name = (argument.name or "argument").replace("_", "-")
    return f"{_command_anchor(parts)}--{name}"


def _option_heading(option: click.Option, ctx: click.Context) -> str:
    help_record = option.get_help_record(ctx)
    if help_record is not None:
        return help_record[0]
    if option.opts:
        return ", ".join((*option.opts, *option.secondary_opts))
    return option.name or "option"


def _option_description(option: click.Option, ctx: click.Context) -> str:
    help_record = option.get_help_record(ctx)
    if help_record is None:
        return ""
    return _strip_click_suffixes(help_record[1])


def _argument_description(argument: click.Argument) -> str:
    if argument.name == "paths":
        return "Paths where pytask looks for task files and configuration."
    return "Positional argument."


def _render_usage(command: click.Command, parts: tuple[str, ...]) -> str:
    ctx = click.Context(command, info_name=" ".join(parts))
    usage = command.get_usage(ctx).strip()
    return usage.removeprefix("Usage: ").strip()


def _command_items(command: click.Command) -> list[tuple[str, click.Command]]:
    commands = getattr(command, "commands", {})
    return [
        (name, subcommand)
        for name, subcommand in sorted(commands.items())
        if not getattr(subcommand, "hidden", False)
    ]


def _command_arguments(
    command: click.Command, ctx: click.Context
) -> list[click.Argument]:
    return [
        param
        for param in command.get_params(ctx)
        if isinstance(param, click.Argument) and not getattr(param, "hidden", False)
    ]


def _command_options(command: click.Command, ctx: click.Context) -> list[click.Option]:
    return [
        param
        for param in command.get_params(ctx)
        if isinstance(param, click.Option) and not getattr(param, "hidden", False)
    ]


def _render_definition_item(
    *,
    anchor: str,
    term: str,
    description: str,
    details: list[str] | None = None,
) -> str:
    escaped_term = html.escape(term, quote=False)
    body = [
        f'<dt id="{anchor}"><a href="#{anchor}"><code>{escaped_term}</code></a></dt>'
    ]

    description_html = html.escape(description)
    extra_html = ""
    if details:
        rendered_details = "<br>".join(html.escape(detail) for detail in details)
        extra_html = f"<p>{rendered_details}</p>"

    body.append(f"<dd><p>{description_html}</p>{extra_html}</dd>")
    return "".join(body)


def _render_argument_section(
    lines: list[str],
    parts: tuple[str, ...],
    argument: click.Argument,
    ctx: click.Context,
) -> None:
    anchor = _argument_anchor(parts, argument)
    metavar = argument.make_metavar(ctx).strip()
    lines.append(
        _render_definition_item(
            anchor=anchor,
            term=metavar,
            description=_argument_description(argument),
        )
    )


def _render_option_section(
    lines: list[str], parts: tuple[str, ...], option: click.Option, ctx: click.Context
) -> None:
    anchor = _option_anchor(parts, option)
    heading = _option_heading(option, ctx)
    description = _option_description(option, ctx)

    metadata: list[str] = []
    default = _format_default(option)
    if default is not None:
        metadata.append(f"Default: {default}")

    if isinstance(option.type, click.Choice):
        choices = ", ".join(option.type.choices)
        metadata.append(f"Accepted values: {choices}")

    lines.append(
        _render_definition_item(
            anchor=anchor,
            term=heading,
            description=description,
            details=metadata or None,
        )
    )


def _render_command(
    lines: list[str], command: click.Command, parts: tuple[str, ...]
) -> None:
    lines.append(f"## {' '.join(parts)} {{ #{_command_anchor(parts)} }}")
    lines.append("")

    description = _command_description(command)
    if description:
        lines.append(description)
        lines.append("")

    lines.append("**Usage**")
    lines.append("")
    lines.append("```console")
    lines.append(_render_usage(command, parts))
    lines.append("```")
    lines.append("")

    subcommands = _command_items(command)
    if subcommands:
        lines.append("**Commands**")
        lines.append("")
        for name, subcommand in subcommands:
            child_parts = (*parts, name)
            summary = _command_description(subcommand)
            line = f"- [`{' '.join(child_parts)}`](#{_command_anchor(child_parts)})"
            if summary:
                line += f": {summary}"
            lines.append(line)
        lines.append("")

    ctx = click.Context(command, info_name=" ".join(parts))
    arguments = _command_arguments(command, ctx)
    if arguments:
        lines.append("**Arguments**")
        lines.append("")
        lines.append('<dl class="cli-reference">')
        for argument in arguments:
            _render_argument_section(lines, parts, argument, ctx)
        lines.append("</dl>")
        lines.append("")

    options = _command_options(command, ctx)
    if options:
        lines.append("**Options**")
        lines.append("")
        lines.append('<dl class="cli-reference">')
        for option in options:
            _render_option_section(lines, parts, option, ctx)
        lines.append("</dl>")
        lines.append("")

    for name, subcommand in subcommands:
        _render_command(lines, subcommand, (*parts, name))


def generate_cli_reference() -> str:
    """Generate the full markdown document."""
    lines = [
        (
            "<!-- Generated by scripts/generate_cli_reference.py. "
            "Do not edit manually. -->"
        ),
        "",
        "# CLI Reference",
        "",
        "Running `pytask` without a subcommand is equivalent to `pytask build`.",
        "",
        "## Command Index",
        "",
    ]

    for name, subcommand in _command_items(cli):
        parts = ("pytask", name)
        summary = _command_description(subcommand)
        line = f"- [`{' '.join(parts)}`](#{_command_anchor(parts)})"
        if summary:
            line += f": {summary}"
        lines.append(line)

    lines.append("")
    _render_command(lines, cli, ("pytask",))
    return "\n".join(lines).rstrip() + "\n"


def _write_reference(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    current = path.read_text() if path.exists() else None
    if current == content:
        return False
    path.write_text(content)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the generated page differs from the checked-in file.",
    )
    args = parser.parse_args()

    content = generate_cli_reference()

    if args.check:
        current = OUT_PATH.read_text() if OUT_PATH.exists() else None
        if current != content:
            return 1
        return 0

    _write_reference(OUT_PATH, content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
