from __future__ import annotations

import textwrap

import pytest

from _pytask.console import render_to_string
from pytask import ExitCode
from pytask import Traceback
from pytask import cli
from pytask import console


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    ("value", "exception", "is_hidden"),
    [
        ("True", "Exception", True),
        ("False", "Exception", False),
        ("lambda exc_info: True", "Exception", True),
        ("lambda exc_info: False", "Exception", False),
        ("lambda exc_info: isinstance(exc_info[1], ValueError)", "ValueError", True),
        ("lambda exc_info: isinstance(exc_info[1], ValueError)", "TypeError", False),
    ],
)
def test_hide_traceback_from_error_report(
    runner, tmp_path, value, exception, is_hidden
):
    source = f"""
    def task_main():
        a = "This variable should not be shown."
        __tracebackhide__ = {value}


        helper()


    def helper():
        raise {exception}
    """
    tmp_path.joinpath("task_main.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--show-locals"])

    assert result.exit_code == ExitCode.FAILED
    assert ("This variable should not be shown." in result.output) is not is_hidden


@pytest.mark.unit
def test_render_traceback_with_string_traceback():
    traceback = Traceback((Exception, Exception("Help"), "String traceback."))
    rendered = render_to_string(traceback, console)
    assert "String traceback." in rendered


@pytest.mark.unit
def test_passing_show_locals():
    traceback = Traceback(
        (Exception, Exception("Help"), "String traceback."), show_locals=True
    )
    assert traceback.show_locals is True
    # Also tests that the class variable has been reset.
    assert traceback._show_locals is False
