import textwrap

import pytest
from pytask import cli


@pytest.mark.parametrize("is_hidden", [True, False])
def test_hide_traceback_from_error_report(runner, tmp_path, is_hidden):
    source = f"""
    def task_main():
        a = "This variable should not be shown."
        __tracebackhide__ = {is_hidden}


        helper()


    def helper():
        raise Exception
    """
    tmp_path.joinpath("task_main.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--show-locals"])

    assert result.exit_code == 1
    assert ("This variable should not be shown." in result.output) is not is_hidden
