"""This module contains the code to format output on the command line."""
import os
import sys
from typing import List

import click
from _pytask.config import hookimpl
from _pytask.shared import convert_truthy_or_falsy_to_bool
from _pytask.shared import get_first_non_none_value
from rich.console import Console
from rich.tree import Tree


_IS_WSL = "IS_WSL" in os.environ or "WSL_DISTRO_NAME" in os.environ
_IS_WINDOWS_TERMINAL = "WT_SESSION" in os.environ
_IS_WINDOWS = sys.platform == "win32"


if (_IS_WINDOWS and not _IS_WINDOWS_TERMINAL) or _IS_WSL:
    _IS_LEGACY_WINDOWS = True
else:
    _IS_LEGACY_WINDOWS = False


_COLOR_SYSTEM = None if _IS_LEGACY_WINDOWS else "auto"


ARROW_DOWN_ICON = "|" if _IS_LEGACY_WINDOWS else "⬇"
FILE_ICON = "" if _IS_LEGACY_WINDOWS else "📄 "
PYTHON_ICON = "" if _IS_LEGACY_WINDOWS else "🐍 "
TASK_ICON = "" if _IS_LEGACY_WINDOWS else "📝 "


console = Console(color_system=_COLOR_SYSTEM)


@hookimpl
def pytask_extend_command_line_interface(cli):
    show_locals_option = click.Option(
        ["--show-locals"],
        is_flag=True,
        default=None,
        help="Show local variables in tracebacks.",
    )
    cli.commands["build"].params.append(show_locals_option)


@hookimpl
def pytask_parse_config(config, config_from_file, config_from_cli):
    config["show_locals"] = get_first_non_none_value(
        config_from_cli,
        config_from_file,
        key="show_locals",
        default=False,
        callback=convert_truthy_or_falsy_to_bool,
    )


def format_strings_as_flat_tree(strings: List[str], title: str, icon: str) -> str:
    """Format list of strings as flat tree."""
    tree = Tree(title)
    for name in strings:
        tree.add(icon + name)

    text = "".join(
        [x.text for x in tree.__rich_console__(console, console.options)][:-1]
    )

    return text


def escape_squared_brackets(string: str) -> str:
    """Escape squared brackets which would be accidentally parsed by rich.

    An example are the ids of parametrized tasks which are suffixed with squared
    brackets surrounding string representations of the parametrized arguments.

    Example
    -------
    >>> escape_squared_brackets("Hello!")
    'Hello!'
    >>> escape_squared_brackets("task_dummy[arg1-arg2]")
    'task_dummy\\\\[arg1-arg2]'

    """
    return string.replace("[", "\\[")
