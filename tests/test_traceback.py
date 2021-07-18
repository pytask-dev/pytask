import textwrap

from pytask import cli


def test_hide_traceback_from_error_report(runner, tmp_path):
    source = """
    def task_main():
        a = "This variable should not be shown."
        __tracebackhide__ = True


        helper()


    def helper():
        raise Exception
    """
    tmp_path.joinpath("task_main.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--show-locals"])

    assert result.exit_code == 1
    assert "This variable should not be shown." not in result.output
