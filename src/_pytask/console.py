"""This module contains the code to format output on the command line."""
import functools
import inspect
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.theme import Theme
from rich.tree import Tree


if TYPE_CHECKING:
    from _pytask.nodes import MetaTask
    from _pytask.outcomes import CollectionOutcome
    from _pytask.outcomes import TaskOutcome


_IS_WSL = "IS_WSL" in os.environ or "WSL_DISTRO_NAME" in os.environ
IS_WINDOWS_TERMINAL = "WT_SESSION" in os.environ
_IS_WINDOWS = sys.platform == "win32"


if (_IS_WINDOWS or _IS_WSL) and not IS_WINDOWS_TERMINAL:
    _IS_LEGACY_WINDOWS = True
else:
    _IS_LEGACY_WINDOWS = False


_COLOR_SYSTEM = None if _IS_LEGACY_WINDOWS else "auto"


_HORIZONTAL_PADDING = (0, 1, 0, 1)


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


theme = Theme(
    {
        "failed": "#BF2D2D",
        "failed.textonly": "#ffffff on #BF2D2D",
        "neutral": "",
        "skipped": "#F4C041",
        "skipped.textonly": "#000000 on #F4C041",
        "success": "#137C39",
        "success.textonly": "#ffffff on #137C39",
        "warning": "#F4C041",
    }
)


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


def create_url_style_for_task(task: "MetaTask", edtior_url_scheme: str) -> Style:
    """Create the style to add a link to a task id."""
    url_scheme = _EDITOR_URL_SCHEMES.get(edtior_url_scheme, edtior_url_scheme)

    info = {
        "path": _get_file(task.function),
        "line_number": _get_source_lines(task.function),
    }

    return Style() if not url_scheme else Style(link=url_scheme.format(**info))


def create_url_style_for_path(path: Path, edtior_url_scheme: str) -> Style:
    """Create the style to add a link to a task id."""
    url_scheme = _EDITOR_URL_SCHEMES.get(edtior_url_scheme, edtior_url_scheme)
    return (
        Style()
        if not url_scheme
        else Style(link=url_scheme.format(path=path, line_number="1"))
    )


def _get_file(function: Callable[..., Any]) -> Path:
    """Get path to module where the function is defined."""
    if isinstance(function, functools.partial):
        return _get_file(function.func)
    else:
        return Path(inspect.getfile(function))


def _get_source_lines(function: Callable[..., Any]) -> int:
    """Get the source line number of the function."""
    if isinstance(function, functools.partial):
        return _get_source_lines(function.func)
    else:
        return inspect.getsourcelines(function)[1]


def unify_styles(*styles: Union[str, Style]) -> Style:
    """Unify styles."""
    parsed_styles = []
    for style in styles:
        if isinstance(style, str) and style in theme.styles:
            parsed_styles.append(theme.styles[style])
        elif isinstance(style, str):
            parsed_styles.append(Style.parse(style))
        else:
            parsed_styles.append(style)
    return Style.combine(parsed_styles)


def create_summary_panel(
    counts: Dict[Enum, int],
    outcome_enum: Union[Type["CollectionOutcome"], Type["TaskOutcome"]],
    description_total: str,
) -> Panel:
    """Create a summary panel."""
    n_total = sum(counts.values())

    grid = Table.grid("", "", "")
    grid.add_row(
        Padding(str(n_total), pad=_HORIZONTAL_PADDING),
        Padding(description_total, pad=_HORIZONTAL_PADDING),
        Padding("", pad=_HORIZONTAL_PADDING),
        style="#ffffff",
    )
    for outcome, value in counts.items():
        if value:
            percentage = f"({100 * value / n_total:.1f}%)"
            grid.add_row(
                Padding(str(value), pad=_HORIZONTAL_PADDING),
                Padding(
                    outcome.description,  # type: ignore[attr-defined]
                    pad=_HORIZONTAL_PADDING,
                ),
                Padding(
                    percentage,
                    pad=_HORIZONTAL_PADDING,
                ),
                style=outcome.style_textonly,  # type: ignore[attr-defined]
            )

    panel = Panel(
        grid,
        title="[bold #ffffff]Summary[/bold #ffffff]",
        expand=False,
        style="none",
        border_style=outcome_enum.FAIL.style
        if counts[outcome_enum.FAIL]
        else outcome_enum.SUCCESS.style,
    )

    return panel
