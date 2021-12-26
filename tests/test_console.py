import inspect
from pathlib import Path

import attr
import pytest
from _pytask.console import create_url_style_for_path
from _pytask.console import create_url_style_for_task
from _pytask.nodes import MetaTask
from rich.style import Style


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
