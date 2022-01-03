import inspect
from pathlib import Path

import attr
import pytest
from _pytask.console import console
from _pytask.console import create_summary_panel
from _pytask.console import create_url_style_for_path
from _pytask.console import create_url_style_for_task
from _pytask.console import format_task_id
from _pytask.console import render_to_string
from _pytask.nodes import create_task_name
from _pytask.nodes import MetaTask
from _pytask.nodes import PythonFunctionTask
from _pytask.outcomes import CollectionOutcome
from _pytask.outcomes import TaskOutcome
from rich.console import Console
from rich.style import Style
from rich.text import Span
from rich.text import Text


def task_func():
    ...


@attr.s
class DummyTask(MetaTask):
    function = attr.ib()

    def state():
        ...

    def execute():
        ...

    def add_report_section():
        ...


_SOURCE_LINE_TASK_FUNC = inspect.getsourcelines(task_func)[1]


@pytest.mark.unit
@pytest.mark.parametrize(
    "edtior_url_scheme, expected",
    [
        ("no_link", ""),
        ("file", "link file:///{path}"),
        ("vscode", f"link vscode://file/{{path}}:{_SOURCE_LINE_TASK_FUNC}"),
        ("pycharm", f"link pycharm://open?file={{path}}&line={_SOURCE_LINE_TASK_FUNC}"),
        (
            f"editor://module={{path}}&line_number={_SOURCE_LINE_TASK_FUNC}",
            f"link editor://module={{path}}&line_number={_SOURCE_LINE_TASK_FUNC}",
        ),
    ],
)
def test_create_url_style_for_task(edtior_url_scheme, expected):
    path = Path(__file__)
    task = DummyTask(task_func)
    style = create_url_style_for_task(task, edtior_url_scheme)
    assert style == Style.parse(expected.format(path=path))


@pytest.mark.unit
@pytest.mark.parametrize(
    "edtior_url_scheme, expected",
    [
        ("no_link", ""),
        ("file", "link file:///{path}"),
        ("vscode", "link vscode://file/{path}:1"),
        ("pycharm", "link pycharm://open?file={path}&line=1"),
        (
            "editor://module={path}&line_number=1",
            "link editor://module={path}&line_number=1",
        ),
    ],
)
def test_create_url_style_for_path(edtior_url_scheme, expected):
    path = Path(__file__)
    style = create_url_style_for_path(path, edtior_url_scheme)
    assert style == Style.parse(expected.format(path=path))


@pytest.mark.unit
@pytest.mark.parametrize(
    "outcome, outcome_enum, total_description",
    [(outcome, TaskOutcome, "description") for outcome in TaskOutcome]
    + [(outcome, CollectionOutcome, "description") for outcome in CollectionOutcome],
)
def test_create_summary_panel(capsys, outcome, outcome_enum, total_description):
    counts = {out: 0 for out in outcome_enum}
    counts[outcome] = 1
    panel = create_summary_panel(counts, outcome_enum, total_description)
    console.print(panel)

    captured = capsys.readouterr().out
    assert "───── Summary ────" in captured
    assert "─┐" in captured or "─╮" in captured
    assert "└─" in captured or "╰─" in captured
    assert outcome.description in captured
    assert "description" in captured


@pytest.mark.unit
@pytest.mark.parametrize(
    "color_system, text, expected",
    [
        (None, "[red]text", "text\n"),
        ("truecolor", "[red]text", "\x1b[31mtext\x1b[0m\n"),
    ],
)
def test_render_to_string(color_system, text, expected):
    console = Console(color_system=color_system)
    result = render_to_string(text, console)
    assert result == expected


_THIS_FILE = Path(__file__)


@pytest.mark.parametrize(
    "base_name, short_name, editor_url_scheme, use_short_name, relative_to, expected",
    [
        pytest.param(
            "task_a",
            None,
            "no_link",
            False,
            None,
            Text(
                _THIS_FILE.as_posix() + "::task_a",
                spans=[
                    Span(0, len(_THIS_FILE.as_posix()) + 2, "dim"),
                    Span(
                        len(_THIS_FILE.as_posix()) + 2,
                        len(_THIS_FILE.as_posix()) + 2 + 6,
                        Style(),
                    ),
                ],
            ),
            id="format full id",
        ),
        pytest.param(
            "task_a",
            "test_console.py::task_a",
            "no_link",
            True,
            None,
            Text(
                "test_console.py::task_a",
                spans=[Span(0, 17, "dim"), Span(17, 23, Style())],
            ),
            id="format short id",
        ),
        pytest.param(
            "task_a",
            None,
            "no_link",
            False,
            _THIS_FILE.parent,
            Text(
                "tests/test_console.py::task_a",
                spans=[Span(0, 23, "dim"), Span(23, 29, Style())],
            ),
            id="format relative to id",
        ),
    ],
)
def test_format_task_id(
    base_name,
    short_name,
    editor_url_scheme,
    use_short_name,
    relative_to,
    expected,
):
    path = _THIS_FILE

    task = PythonFunctionTask(
        base_name, create_task_name(path, base_name), path, task_func
    )
    if short_name is not None:
        task.short_name = short_name

    result = format_task_id(task, editor_url_scheme, use_short_name, relative_to)
    assert result == expected
