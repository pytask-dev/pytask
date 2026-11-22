from __future__ import annotations

import textwrap

import pytest
from rich.traceback import Traceback as RichTraceback

from _pytask.console import render_to_string
from pytask import ExitCode
from pytask import Traceback
from pytask import cli
from pytask import console


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


def test_render_traceback_with_string_traceback():
    traceback = Traceback((Exception, Exception("Help"), "String traceback."))
    rendered = render_to_string(traceback, console)
    assert "String traceback." in rendered


def test_render_extracted_rich_trace():
    try:
        msg = "worker failure"
        raise ValueError(msg)  # noqa: TRY301
    except ValueError as exc:
        trace = RichTraceback.extract(type(exc), exc, exc.__traceback__)
        traceback = Traceback((type(exc), exc, trace))

    rendered = render_to_string(traceback, console)
    assert "ValueError: worker failure" in rendered
    assert "test_render_extracted_rich_trace" in rendered


def test_passing_show_locals():
    traceback = Traceback(
        (Exception, Exception("Help"), "String traceback."),
        show_locals=True,
    )
    assert traceback.show_locals is True
    # Also tests that the class variable has been reset.
    assert traceback._show_locals is False


def test_render_traceback_preserves_implicit_exception_context():
    def raise_inner():
        msg = "inner"
        raise ValueError(msg)

    def raise_with_context():
        try:
            raise_inner()
        except ValueError:
            msg = "outer"
            raise RuntimeError(msg)  # noqa: B904

    with pytest.raises(RuntimeError) as exc_info:
        raise_with_context()

    exc = exc_info.value
    assert exc.__context__ is not None
    assert not exc.__suppress_context__

    render_to_string(Traceback((type(exc), exc, exc.__traceback__)), console)

    assert exc.__context__ is not None
    assert not exc.__suppress_context__
