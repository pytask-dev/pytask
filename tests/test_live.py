import textwrap

import pytest
from pytask import cli


@pytest.mark.end_to_end
@pytest.mark.parametrize("verbose", [False, True])
def test_verbose_mode_execution(tmp_path, runner, verbose):
    source = "def task_dummy(): pass"
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    args = [tmp_path.as_posix()]
    if verbose:
        args.append("-v")
    result = runner.invoke(cli, args)

    assert ("Task" in result.output) is verbose
    assert ("Outcome" in result.output) is verbose
    assert ("┌───" in result.output) is verbose
    assert ("task_dummy.py::task_dummy" in result.output) is verbose
