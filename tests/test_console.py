from __future__ import annotations

import inspect
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import pytest
from _pytask.console import _get_source_lines
from _pytask.console import create_summary_panel
from _pytask.console import create_url_style_for_path
from _pytask.console import create_url_style_for_task
from _pytask.console import format_node_name
from _pytask.console import format_task_name
from _pytask.console import get_file
from _pytask.console import render_to_string
from pytask import CollectionOutcome
from pytask import PathNode
from pytask import PythonNode
from pytask import Task
from pytask import TaskOutcome
from pytask import console
from rich.console import Console
from rich.style import Style
from rich.text import Span
from rich.text import Text

from tests._test_console_helpers import empty_decorator


def task_func(): ...


_SOURCE_LINE_TASK_FUNC = inspect.getsourcelines(task_func)[1]


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("edtior_url_scheme", "expected"),
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
    style = create_url_style_for_task(task_func, edtior_url_scheme)
    assert style == Style.parse(expected.format(path=path))


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("edtior_url_scheme", "expected"),
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


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("outcome", "outcome_enum", "total_description"),
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


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("color_system", "text", "strip_styles", "expected"),
    [
        (None, "[red]text", False, "text\n"),
        ("truecolor", "[red]text", False, "\x1b[31mtext\x1b[0m\n"),
        ("truecolor", "[red]text", True, "text\n"),
    ],
)
def test_render_to_string(color_system, text, strip_styles, expected):
    console = Console(color_system=color_system)
    result = render_to_string(text, console=console, strip_styles=strip_styles)
    assert result == expected


_THIS_FILE = Path(__file__)


@pytest.mark.unit()
@pytest.mark.parametrize(
    (
        "base_name",
        "editor_url_scheme",
        "expected",
    ),
    [
        pytest.param(
            "task_a",
            "no_link",
            Text(
                _THIS_FILE.as_posix() + "::task_a",
                spans=[Span(0, len(_THIS_FILE.as_posix()) + 2, "dim")],
            ),
            id="format full id",
        )
    ],
)
def test_format_task_id(
    base_name,
    editor_url_scheme,
    expected,
):
    path = _THIS_FILE

    task = Task(base_name=base_name, path=path, function=task_func)
    result = format_task_name(task, editor_url_scheme)
    assert result == expected


_ROOT = Path.cwd()


@pytest.mark.integration()
@pytest.mark.parametrize(
    ("node", "paths", "expectation", "expected"),
    [
        pytest.param(
            PathNode.from_path(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("alternative_src")],
            does_not_raise(),
            Text("pytask/src/module.py"),
            id="Common path found for PathNode not in 'paths' and 'paths'",
        ),
        pytest.param(
            PathNode.from_path(_ROOT.joinpath("top/src/module.py")),
            [_ROOT.joinpath("top/src")],
            does_not_raise(),
            Text("src/module.py"),
            id="make filepathnode relative to 'paths'.",
        ),
        pytest.param(
            PythonNode(name="hello", value=None),
            [_ROOT],
            does_not_raise(),
            Text("hello"),
            id="PythonNode with name",
        ),
        pytest.param(
            PythonNode(name=_ROOT.as_posix() + "/task_a.py::task_a::a", value=None),
            [_ROOT],
            does_not_raise(),
            Text("pytask/task_a.py::task_a::a"),
            id="PythonNode with automatically assigned name",
        ),
    ],
)
def test_reduce_node_name(node, paths, expectation, expected):
    with expectation:
        result = format_node_name(node, paths)
        assert result == expected


exec("__unknown_lambda = lambda x: x")  # noqa: S102


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("task_func", "skipped_paths", "expected"),
    [
        (task_func, None, _THIS_FILE),
        (
            empty_decorator(task_func),
            None,
            _THIS_FILE.parent.joinpath("_test_console_helpers.py"),
        ),
        (
            empty_decorator(task_func),
            [_THIS_FILE.parent.joinpath("_test_console_helpers.py")],
            _THIS_FILE,
        ),
        (lambda x: x, None, Path(__file__)),
        (__unknown_lambda, None, Path(__file__)),  # noqa: F821
    ],
)
def test_get_file(task_func, skipped_paths, expected):
    result = get_file(task_func, skipped_paths)
    assert result == expected


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("task_func", "expected"),
    [
        (task_func, _SOURCE_LINE_TASK_FUNC),
        (empty_decorator(task_func), _SOURCE_LINE_TASK_FUNC),
    ],
)
def test_get_source_lines(task_func, expected):
    result = _get_source_lines(task_func)
    assert result == expected
