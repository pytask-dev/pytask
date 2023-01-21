from __future__ import annotations

import textwrap

import pytest
from pytask import cli
from pytask import ExitCode


@pytest.mark.end_to_end()
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
