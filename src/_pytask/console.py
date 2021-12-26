"""This module contains the code to format output on the command line."""
import functools
import inspect
import os
import sys
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import TYPE_CHECKING

from rich.console import Console
from rich.theme import Theme
from rich.tree import Tree


if TYPE_CHECKING:
    from _pytask.nodes import MetaTask


_IS_WSL = "IS_WSL" in os.environ or "WSL_DISTRO_NAME" in os.environ
IS_WINDOWS_TERMINAL = "WT_SESSION" in os.environ
_IS_WINDOWS = sys.platform == "win32"


if (_IS_WINDOWS or _IS_WSL) and not IS_WINDOWS_TERMINAL:
    _IS_LEGACY_WINDOWS = True
else:
    _IS_LEGACY_WINDOWS = False


_COLOR_SYSTEM = None if _IS_LEGACY_WINDOWS else "auto"


ARROW_DOWN_ICON = "|" if _IS_LEGACY_WINDOWS else "⬇"
FILE_ICON = "" if _IS_LEGACY_WINDOWS else "📄 "
PYTHON_ICON = "" if _IS_LEGACY_WINDOWS else "🐍 "
TASK_ICON = "" if _IS_LEGACY_WINDOWS else "📝 "


_EDITOR_URL_SCHEMES: Dict[str, str] = {
    "no_link": "",
    "file": "file:///{path}",
    "vscode": "vscode://file/{path}:{line_number}",
    "pycharm": "pycharm://open?file={path}&line={line_number}",
}


theme = Theme({"warning": "yellow"})


console = Console(theme=theme, color_system=_COLOR_SYSTEM)


def format_strings_as_flat_tree(strings: Iterable[str], title: str, icon: str) -> str:
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


def create_url_style_for_task(task: "MetaTask", edtior_url_scheme: str) -> str:
    """Create the style to add a link to a task id."""
    url_scheme = _EDITOR_URL_SCHEMES.get(edtior_url_scheme, edtior_url_scheme)

    info = {
        "path": _get_file(task.function),
        "line_number": inspect.getsourcelines(task.function)[1],
    }

    return "" if not url_scheme else "link " + url_scheme.format(**info)


def _get_file(function: Callable[..., Any]) -> Path:
    """Get path to module where the function is defined."""
    if isinstance(function, functools.partial):
        return _get_file(function.func)
    else:
        return Path(inspect.getfile(function))
