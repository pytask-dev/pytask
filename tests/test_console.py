import textwrap

import pytest
from pytask import cli


@pytest.mark.end_to_end
def test_printing_of_local_variables(tmp_path, runner):
    source = """
    def task_dummy():
        a = 1
        helper()

    def helper():
        b = 2
        raise Exception
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--show-locals"])
    assert result.exit_code == 1

    captured = result.output
    assert " locals " in captured
    assert "a = 1" in captured
    assert "b = 2" in captured
