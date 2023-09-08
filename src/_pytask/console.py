"""Contains the code to format output on the command line."""
from __future__ import annotations

import functools
import inspect
import os
import sys
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Iterable
from typing import TYPE_CHECKING

import rich
from _pytask.nodes import Task
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.tree import Tree


if TYPE_CHECKING:
    from _pytask.node_protocols import PTask
    from enum import Enum
    from _pytask.outcomes import CollectionOutcome
    from _pytask.outcomes import TaskOutcome


__all__ = [
    "create_summary_panel",
    "create_url_style_for_task",
    "create_url_style_for_path",
    "console",
    "format_task_name",
    "format_strings_as_flat_tree",
    "get_file",
    "is_jupyter",
    "render_to_string",
    "unify_styles",
]


_IS_WSL = "IS_WSL" in os.environ or "WSL_DISTRO_NAME" in os.environ
IS_WINDOWS_TERMINAL = "WT_SESSION" in os.environ
_IS_WINDOWS = sys.platform == "win32"


if (_IS_WINDOWS or _IS_WSL) and not IS_WINDOWS_TERMINAL:
    _IS_LEGACY_WINDOWS = True
else:
    _IS_LEGACY_WINDOWS = False


_COLOR_SYSTEM = None if _IS_LEGACY_WINDOWS else "auto"


_HORIZONTAL_PADDING = (0, 1, 0, 1)


_SKIPPED_PATHS = [Path(__file__).parent.joinpath("debugging.py")]
"""List[Path]: List of paths to skip when tracing down the path to the source of a task
function.

"""

ARROW_DOWN_ICON = "|" if _IS_LEGACY_WINDOWS else "⬇"
FILE_ICON = "" if _IS_LEGACY_WINDOWS else "📄 "
PYTHON_ICON = "" if _IS_LEGACY_WINDOWS else "🐍 "
TASK_ICON = "" if _IS_LEGACY_WINDOWS else "📝 "


_EDITOR_URL_SCHEMES: dict[str, str] = {
    "no_link": "",
    "file": "file:///{path}",
    "vscode": "vscode://file/{path}:{line_number}",
    "pycharm": "pycharm://open?file={path}&line={line_number}",
}


theme = Theme(
    {
        # Statuses
        "failed": "#BF2D2D",
        "failed.textonly": "#f2f2f2 on #BF2D2D",
        "neutral": "",
        "skipped": "#F4C041",
        "skipped.textonly": "#0c0c0c on #F4C041",
        "success": "#137C39",
        "success.textonly": "#f2f2f2 on #137C39",
        "warning": "#F4C041",
        # Help page.
        "command": "bold #137C39",
        "option": "bold #F4C041",
        "switch": "bold #D54523",
        "metavar": "bold #FFFF00",
    }
)


console: Console = Console(theme=theme, color_system=_COLOR_SYSTEM)


def render_to_string(
    text: str | Text,
    *,
    console: Console | None = None,
    strip_styles: bool = False,
) -> str:
    """Render text with rich to string including ANSI codes, etc..

    This function allows to render text with is not automatically printed with rich. For
    example, render warnings with colors or text in exceptions.

    """
    if console is None:
        console = rich.get_console()

    segments = console.render(text)

    output = []
    if console.no_color and console._color_system:
        segments = Segment.remove_color(segments)

    if strip_styles:
        segments = Segment.strip_styles(segments)

    for segment in segments:
        if segment.style:
            output.append(
                segment.style.render(
                    segment.text,
                    color_system=console._color_system,
                    legacy_windows=console.legacy_windows,
                )
            )
        else:
            output.append(segment.text)

    return "".join(output)


def format_task_name(task: PTask, editor_url_scheme: str) -> Text:
    """Format a task id."""
    if task.function is None:
        url_style = Style()
    else:
        url_style = create_url_style_for_task(task.function, editor_url_scheme)

    if isinstance(task, Task):
        path, task_name = task.display_name.split("::")
        task_id = Text.assemble(
            Text(path + "::", style="dim"), Text(task_name, style=url_style)
        )
    else:
        name = getattr(task, "display_name", task.name)
        task_id = Text(name, style=url_style)
    return task_id


def format_strings_as_flat_tree(strings: Iterable[str], title: str, icon: str) -> str:
    """Format list of strings as flat tree."""
    tree = Tree(title)
    for name in strings:
        tree.add(Text.assemble(icon, name))
    return render_to_string(tree, console=console)


def create_url_style_for_task(
    task_function: Callable[..., Any], edtior_url_scheme: str
) -> Style:
    """Create the style to add a link to a task id."""
    url_scheme = _EDITOR_URL_SCHEMES.get(edtior_url_scheme, edtior_url_scheme)

    if not url_scheme:
        return Style()

    try:
        info = {
            "path": get_file(task_function),
            "line_number": _get_source_lines(task_function),
        }
    except (OSError, TypeError):
        style = Style()
    else:
        style = Style(link=url_scheme.format(**info))

    return style


def create_url_style_for_path(path: Path, edtior_url_scheme: str) -> Style:
    """Create the style to add a link to a task id."""
    url_scheme = _EDITOR_URL_SCHEMES.get(edtior_url_scheme, edtior_url_scheme)
    return (
        Style()
        if not url_scheme
        else Style(link=url_scheme.format(path=path, line_number="1"))
    )


def get_file(
    function: Callable[..., Any], skipped_paths: list[Path] | None = None
) -> Path:
    """Get path to module where the function is defined.

    When the ``pdb`` or ``trace`` mode is activated, every task function is wrapped with
    a decorator which we need to skip to get to the underlying task function. Thus, the
    special case.

    """
    if skipped_paths is None:
        skipped_paths = _SKIPPED_PATHS

    if isinstance(function, functools.partial):
        return get_file(function.func)
    if (
        hasattr(function, "__wrapped__")
        and Path(inspect.getsourcefile(function)) in skipped_paths
    ):
        return get_file(function.__wrapped__)
    return Path(inspect.getsourcefile(function))


def _get_source_lines(function: Callable[..., Any]) -> int:
    """Get the source line number of the function."""
    if isinstance(function, functools.partial):
        return _get_source_lines(function.func)
    if hasattr(function, "__wrapped__"):
        return _get_source_lines(function.__wrapped__)
    return inspect.getsourcelines(function)[1]


def unify_styles(*styles: str | Style) -> Style:
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
    counts: dict[Enum, int],
    outcome_enum: type[CollectionOutcome | TaskOutcome],
    description_total: str,
) -> Panel:
    """Create a summary panel."""
    n_total = sum(counts.values())

    grid = Table.grid("", "", "")
    grid.add_row(
        Padding(str(n_total), pad=_HORIZONTAL_PADDING),
        Padding(description_total, pad=_HORIZONTAL_PADDING),
        Padding("", pad=_HORIZONTAL_PADDING),
        style="#f2f2f2",
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

    return Panel(
        grid,
        title="[bold #f2f2f2]Summary[/]",
        expand=False,
        style="none",
        border_style=outcome_enum.FAIL.style
        if counts[outcome_enum.FAIL]
        else outcome_enum.SUCCESS.style,
    )


def is_jupyter() -> bool:  # pragma: no cover
    """Check if we're running in a Jupyter notebook.

    Copied from rich.

    """
    try:
        get_ipython  # type: ignore[name-defined]  # noqa: B018
    except NameError:
        return False
    ipython = get_ipython()  # type: ignore[name-defined]  # noqa: F821
    shell = ipython.__class__.__name__
    if (
        "google.colab" in str(ipython.__class__)
        or os.getenv("DATABRICKS_RUNTIME_VERSION")
        or shell == "ZMQInteractiveShell"
    ):
        return True  # Jupyter notebook or qtconsole
    if shell == "TerminalInteractiveShell":
        return False  # Terminal running IPython
    return False  # Other type (?)
