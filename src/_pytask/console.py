"""This module contains the code to format output on the command line."""
import os
import sys
from typing import List

from rich.console import Console
from rich.status import Status
from rich.tree import Tree


_IS_WSL = "IS_WSL" in os.environ or "WSL_DISTRO_NAME" in os.environ
_IS_WINDOWS_TERMINAL = "WT_SESSION" in os.environ
_IS_WINDOWS = sys.platform == "win32"


if (_IS_WINDOWS or _IS_WSL) and not _IS_WINDOWS_TERMINAL:
    _IS_LEGACY_WINDOWS = True
else:
    _IS_LEGACY_WINDOWS = False


_COLOR_SYSTEM = None if _IS_LEGACY_WINDOWS else "auto"


ARROW_DOWN_ICON = "|" if _IS_LEGACY_WINDOWS else "⬇"
FILE_ICON = "" if _IS_LEGACY_WINDOWS else "📄 "
PYTHON_ICON = "" if _IS_LEGACY_WINDOWS else "🐍 "
TASK_ICON = "" if _IS_LEGACY_WINDOWS else "📝 "


console = Console(color_system=_COLOR_SYSTEM)


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


def generate_collection_status(n_collected_tasks):
    """Generate the status object to display the progress during collection."""
    return Status(
        f"Collected {n_collected_tasks} tasks.", refresh_per_second=4, spinner="dots"
    )
