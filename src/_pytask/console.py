"""This module contains the code to format output on the command line."""
import os
import sys
from typing import List

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


def format_strings_as_flat_tree(strings: List[str], title: str, icon: str) -> str:
    """Format list of strings as flat tree."""
    tree = Tree(title)
    for name in strings:
        tree.add(icon + name)

    text = "".join(
        [x.text for x in tree.__rich_console__(console, console.options)][:-1]
    )

    return text
