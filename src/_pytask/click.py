"""Contains code related to click."""

from __future__ import annotations

import importlib.metadata
import inspect
from enum import Enum
from gettext import gettext as _
from gettext import ngettext
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import TypeVar

import click
from click import Choice
from click import Command
from click import Context
from click import Parameter
from click_default_group import DefaultGroup
from rich.highlighter import RegexHighlighter
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from _pytask import __version__ as version
from _pytask.console import console
from _pytask.console import create_panel_title

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence


__all__ = ["ColoredCommand", "ColoredGroup", "EnumChoice"]


if importlib.metadata.version("click") < "8.2":
    from click.parser import split_opt

    class EnumChoice(Choice):  # type: ignore[type-arg, unused-ignore]
        """An enum-based choice type.

        The implementation is copied from https://github.com/pallets/click/pull/2210 and
        related discussion can be found in https://github.com/pallets/click/issues/605.

        In contrast to using :class:`click.Choice`, using this type ensures that the
        error message does not show the enum members.

        In contrast to the proposed implementation in the PR, this implementation does
        not use the members than rather the values of the enum.

        """

        def __init__(self, enum_type: type[Enum], case_sensitive: bool = True) -> None:
            super().__init__(
                choices=[element.value for element in enum_type],
                case_sensitive=case_sensitive,
            )
            self.enum_type = enum_type

        def convert(
            self, value: Any, param: Parameter | None, ctx: Context | None
        ) -> Any:
            if isinstance(value, Enum):
                value = value.value
            value = super().convert(value=value, param=param, ctx=ctx)
            if value is None:
                return None
            return self.enum_type(value)

else:
    from click.parser import (  # type: ignore[attr-defined, no-redef, unused-ignore]
        _split_opt as split_opt,
    )

    ParamTypeValue = TypeVar("ParamTypeValue")

    class EnumChoice(Choice):  # type: ignore[no-redef, type-arg, unused-ignore]
        def __init__(
            self, choices: Iterable[ParamTypeValue], case_sensitive: bool = False
        ) -> None:
            super().__init__(choices=choices, case_sensitive=case_sensitive)  # type: ignore[arg-type, unused-ignore]


class _OptionHighlighter(RegexHighlighter):
    """A highlighter for help texts."""

    highlights: ClassVar = [  # type: ignore[misc]
        r"(?P<switch>\-\w)\b",
        r"(?P<option>\-\-[\w\-]+)",
        r"\-\-[\w\-]+(?P<metavar>[ |=][\w\.:]+)",
    ]


class ColoredGroup(DefaultGroup):
    """A command group with colored help pages."""

    def format_help(
        self: DefaultGroup,
        ctx: Context,
        formatter: Any,  # noqa: ARG002
    ) -> None:
        """Format the help text."""
        highlighter = _OptionHighlighter()

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
                title=create_panel_title("Commands"),
                title_align="left",
                border_style="grey37",
            )
        )

        _print_options(self, ctx)

        console.print(
            Padding(
                "[bold #FF0000]♥[/] [#f2f2f2]https://pytask-dev.readthedocs.io[/]",
                (0, 3, 0, 0),
            ),
            justify="right",
        )


def _iter_params_for_processing(
    invocation_order: Sequence[Parameter], declaration_order: Sequence[Parameter]
) -> list[Parameter]:
    def sort_key(item: Parameter) -> tuple[bool, float]:
        # Hardcode the order of the config and paths parameters so that they are always
        # processed first even if other eager parameters are chosen. The rest follows
        # https://click.palletsprojects.com/en/8.1.x/advanced/#callback-evaluation-order.
        if item.name == "paths":
            return False, -3

        if item.name == "config":
            return False, -2

        if item.name == "hook_module":
            return False, -1

        try:
            idx: float = invocation_order.index(item)
        except ValueError:
            idx = float("inf")

        return not item.is_eager, idx

    return sorted(declaration_order, key=sort_key)


class ColoredCommand(Command):
    """A command with colored help pages."""

    def parse_args(self, ctx: Context, args: list[str]) -> list[str]:
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()

        parser = self.make_parser(ctx)
        opts, args, param_order = parser.parse_args(args=args)

        for param in _iter_params_for_processing(param_order, self.get_params(ctx)):
            value, args = param.handle_parse_result(ctx, opts, args)

        if args and not ctx.allow_extra_args and not ctx.resilient_parsing:
            ctx.fail(
                ngettext(
                    "Got unexpected extra argument ({args})",
                    "Got unexpected extra arguments ({args})",
                    len(args),
                ).format(args=" ".join(map(str, args)))
            )

        ctx.args = args
        ctx._opt_prefixes.update(parser._opt_prefixes)
        return args

    def format_help(
        self: Command,
        ctx: Context,
        formatter: Any,  # noqa: ARG002
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

        _print_options(self, ctx)

        console.print(
            Padding(
                "[bold #FF0000]♥[/] [#f2f2f2]https://pytask-dev.readthedocs.io[/]",
                (0, 3, 0, 0),
            ),
            justify="right",
        )


def _print_options(group_or_command: Command | DefaultGroup, ctx: Context) -> None:
    """Print options formatted with a table in a panel."""
    highlighter = _OptionHighlighter()

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
        elif len(param.opts) == 2:  # noqa: PLR2004
            opt1 = highlighter(param.opts[0])
            opt2 = highlighter(param.opts[1])
        elif len(param.opts) == 1 == len(param.secondary_opts):
            opt1 = Text("")
            opt2 = highlighter(param.opts[0] + "/" + param.secondary_opts[0])
        elif "--" in param.opts[0]:
            opt1 = Text("")
            opt2 = highlighter(param.opts[0])
        else:
            opt1 = highlighter(param.opts[0])
            opt2 = Text("")

        if param.metavar:
            opt2 += Text(f" {param.metavar}", style="metavar")
        elif isinstance(param.type, click.Choice):
            choices = "[" + "|".join(param.type.choices) + "]"
            opt2 += Text(f" {choices}", style="metavar", overflow="fold")

        help_text = _format_help_text(param, ctx)

        options_table.add_row(opt1, opt2, highlighter(help_text))

    console.print(
        Panel(
            options_table,
            title=create_panel_title("Options"),
            title_align="left",
            border_style="grey37",
        )
    )


def _format_help_text(  # noqa: C901, PLR0912, PLR0915
    param: Parameter, ctx: Context
) -> Text:
    """Format the help of a click parameter.

    A large chunk of the function is copied from
    :meth:`click.core.Option.get_help_record` to support styling, show values of enums,
    etc..

    """
    help_text = Text.from_markup(getattr(param, "help", None) or "")
    extra = []

    if getattr(param, "show_envvar", None):  # pragma: no cover
        envvar = getattr(param, "envvar", None)

        if envvar is None and (
            getattr(param, "allow_from_autoenv", None)
            and ctx.auto_envvar_prefix is not None
            and param.name is not None
        ):
            envvar = f"{ctx.auto_envvar_prefix}_{param.name.upper()}"

        if envvar is not None:
            var_str = (
                envvar if isinstance(envvar, str) else ", ".join(str(d) for d in envvar)
            )
            extra.append(_("env var: {var}").format(var=var_str))

    # Temporarily enable resilient parsing to avoid type casting
    # failing for the default. Might be possible to extend this to
    # help formatting in general.
    resilient = ctx.resilient_parsing
    ctx.resilient_parsing = True

    try:
        default_value = param.get_default(ctx, call=False)
    finally:
        ctx.resilient_parsing = resilient

    show_default = False
    show_default_is_str = False

    if param.show_default is not None:  # type: ignore[attr-defined]
        if isinstance(param.show_default, str):  # type: ignore[attr-defined]
            show_default_is_str = show_default = True
        else:
            show_default = param.show_default  # type: ignore[attr-defined]
    elif ctx.show_default is not None:
        show_default = ctx.show_default

    if show_default_is_str or (show_default and (default_value is not None)):
        if show_default_is_str:
            default_string = param.show_default  # type: ignore[attr-defined]
        elif isinstance(default_value, (list, tuple)):
            default_string = ", ".join(str(d) for d in default_value)
        elif inspect.isfunction(default_value):
            default_string = _("dynamic")
        elif param.is_bool_flag and param.secondary_opts:  # type: ignore[attr-defined]
            # For boolean flags that have distinct True/False opts,
            # use the opt without prefix instead of the value.
            default_string = split_opt(  # type: ignore[operator, unused-ignore]
                (param.opts if param.default else param.secondary_opts)[0]
            )[1]
        elif (
            param.is_bool_flag  # type: ignore[attr-defined]
            and not param.secondary_opts
            and not default_value
        ):
            default_string = ""
        elif isinstance(default_value, Enum):
            default_string = str(default_value.value)
        else:
            default_string = str(default_value)

        if default_string:
            extra.append(_("default: {default}").format(default=default_string))

    if (
        isinstance(param.type, click.types._NumberRangeBase)
        # skip count with default range type
        and not (
            param.count  # type: ignore[attr-defined]
            and param.type.min == 0
            and param.type.max is None
        )
    ):
        range_str = _describe_range(param.type)

        if range_str:
            extra.append(range_str)

    if param.required:
        extra.append(_("required"))

    if extra:
        extra_str = "; ".join(extra)
        full_help_text = help_text + Text.from_markup(rf" [dim]\[{extra_str}][/]")
    else:
        full_help_text = help_text

    return full_help_text


def _describe_range(
    param_type: click.types._NumberBaseRange,  # type: ignore[name-defined]
) -> str:
    """Describe the range for use in help text.

    It differs from the :meth:`click.types._NumberRangeBase._describe_range()` because
    intervals are always ordered as on the number line.

    Examples
    --------
    >>> from click.types import _NumberRangeBase
    >>> _describe_range(_NumberRangeBase(min=1))
    '1<=x'
    >>> _describe_range(_NumberRangeBase(max=2))
    'x<=2'

    """
    if param_type.min is None:
        op = "<" if param_type.max_open else "<="
        return f"x{op}{param_type.max}"

    if param_type.max is None:
        op = "<" if param_type.min_open else "<="
        return f"{param_type.min}{op}x"

    lop = "<" if param_type.min_open else "<="
    rop = "<" if param_type.max_open else "<="
    return f"{param_type.min}{lop}x{rop}{param_type.max}"
