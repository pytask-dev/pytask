from __future__ import annotations

import textwrap

import pytest
from _pytask.outcomes import ExitCode
from pytask import cli


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "value, is_hidden",
    [
        (True, True),
        (False, False),
        ("lambda exc_info: True", True),
        ("lambda exc_info: False", False),
    ],
)
def test_hide_traceback_from_error_report(runner, tmp_path, value, is_hidden):
    source = f"""
    def task_main():
        a = "This variable should not be shown."
        __tracebackhide__ = {value}


        helper()


    def helper():
        raise Exception
    """
    tmp_path.joinpath("task_main.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--show-locals"])

    assert result.exit_code == ExitCode.FAILED
    assert ("This variable should not be shown." in result.output) is not is_hidden
