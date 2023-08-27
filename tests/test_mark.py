from __future__ import annotations

import subprocess
import sys
import textwrap

import pytask
import pytest
from pytask import cli
from pytask import ExitCode
from pytask import main
from pytask import MarkGenerator


@pytest.mark.unit()
@pytest.mark.parametrize("attribute", ["hookimpl", "mark"])
def test_mark_exists_in_pytask_namespace(attribute):
    assert attribute in sys.modules["pytask"].__all__


@pytest.mark.unit()
def test_pytask_mark_notcallable() -> None:
    mark = MarkGenerator()
    with pytest.raises(TypeError):
        mark()


@pytest.mark.unit()
@pytest.mark.filterwarnings("ignore:Unknown pytask.mark.foo")
def test_mark_with_param():
    def some_function():  # pragma: no cover
        pass

    class SomeClass:
        pass

    assert pytask.mark.foo(some_function) is some_function
    marked_with_args = pytask.mark.foo.with_args(some_function)
    assert marked_with_args is not some_function

    assert pytask.mark.foo(SomeClass) is SomeClass
    assert pytask.mark.foo.with_args(SomeClass) is not SomeClass


@pytest.mark.unit()
def test_pytask_mark_name_starts_with_underscore():
    mark = MarkGenerator()
    with pytest.raises(AttributeError):
        _ = mark._some_name


@pytest.mark.end_to_end()
def test_markers_command(tmp_path, runner):
    toml = """
    [tool.pytask.ini_options]
    markers = ["a1", "a2", "nodescription"]
    """
    config_path = tmp_path.joinpath("pyproject.toml")
    config_path.write_text(textwrap.dedent(toml))

    result = runner.invoke(cli, ["markers", "-c", config_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    for out in ("pytask.mark.a1", "pytask.mark.a2", "pytask.mark.nodescription"):
        assert out in result.output


@pytest.mark.end_to_end()
def test_ini_markers_whitespace(runner, tmp_path):
    tmp_path.joinpath("pyproject.toml").write_text(
        "[tool.pytask.ini_options]\nmarkers = {'a1 ' = 'this is a whitespace marker'}"
    )
    source = """
    import pytask
    @pytask.mark.a1
    def task_markers():
        assert True
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
@pytest.mark.filterwarnings("ignore:Unknown pytask.mark.")
@pytest.mark.parametrize(
    ("expr", "expected_passed"),
    [
        ("xyz", ["task_one"]),
        ("(((  xyz))  )", ["task_one"]),
        ("not not xyz", ["task_one"]),
        ("xyz and xyz2", []),
        ("xyz2", ["task_two"]),
        ("xyz or xyz2", ["task_one", "task_two"]),
    ],
)
def test_mark_option(tmp_path, expr: str, expected_passed: str) -> None:
    tmp_path.joinpath("task_module.py").write_text(
        textwrap.dedent(
            """
            import pytask
            @pytask.mark.xyz
            def task_one():
                pass
            @pytask.mark.xyz2
            def task_two():
                pass
            """
        )
    )
    session = main({"paths": tmp_path, "marker_expression": expr})

    tasks_that_run = [
        report.task.name.rsplit("::")[1]
        for report in session.execution_reports
        if not report.exc_info
    ]
    assert set(tasks_that_run) == set(expected_passed)


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("expr", "expected_passed"),
    [
        ("interface", ["task_interface"]),
        ("not interface", ["task_nointer", "task_pass", "task_no_1", "task_no_2"]),
        ("pass", ["task_pass"]),
        ("not pass", ["task_interface", "task_nointer", "task_no_1", "task_no_2"]),
        (
            "not not not (pass)",
            ["task_interface", "task_nointer", "task_no_1", "task_no_2"],
        ),
        ("no_1 or no_2", ["task_no_1", "task_no_2"]),
        ("not (no_1 or no_2)", ["task_interface", "task_nointer", "task_pass"]),
    ],
)
def test_keyword_option_custom(tmp_path, expr: str, expected_passed: str) -> None:
    tmp_path.joinpath("task_module.py").write_text(
        textwrap.dedent(
            """
            def task_interface():
                pass
            def task_nointer():
                pass
            def task_pass():
                pass
            def task_no_1():
                pass
            def task_no_2():
                pass
            """
        )
    )
    session = main({"paths": tmp_path, "expression": expr})
    assert session.exit_code == ExitCode.OK

    tasks_that_run = [
        report.task.name.rsplit("::")[1]
        for report in session.execution_reports
        if not report.exc_info
    ]
    assert set(tasks_that_run) == set(expected_passed)


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("expr", "expected_passed"),
    [
        ("arg0", ["task_func[arg0]"]),
        ("1.3", ["task_func[1.3]"]),
        ("2-3", ["task_func[2-3]"]),
    ],
)
def test_keyword_option_parametrize(tmp_path, expr: str, expected_passed: str) -> None:
    source = """
    import pytask

    for arg in [None, 1.3, "2-3"]:

        @pytask.mark.task
        def task_func(arg=arg):
            pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path, "expression": expr})
    assert session.exit_code == ExitCode.OK

    tasks_that_run = [
        report.task.name.rsplit("::")[1]
        for report in session.execution_reports
        if not report.exc_info
    ]
    assert set(tasks_that_run) == set(expected_passed)


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("expr", "expected_error"),
    [
        (
            "foo or",
            "at column 7: expected not OR left parenthesis OR identifier; got end of "
            "input",
        ),
        (
            "foo or or",
            "at column 8: expected not OR left parenthesis OR identifier; got or",
        ),
        (
            "(foo",
            "at column 5: expected right parenthesis; got end of input",
        ),
        (
            "foo bar",
            "at column 5: expected end of input; got identifier",
        ),
        (
            "or or",
            "at column 1: expected not OR left parenthesis OR identifier; got or",
        ),
        (
            "not or",
            "at column 5: expected not OR left parenthesis OR identifier; got or",
        ),
    ],
)
@pytest.mark.parametrize("option", ["expression", "marker_expression"])
def test_keyword_option_wrong_arguments(
    tmp_path, capsys, option: str, expr: str, expected_error: str
) -> None:
    tmp_path.joinpath("task_module.py").write_text(
        textwrap.dedent("def task_func(arg): pass")
    )
    session = main({"paths": tmp_path, option: expr})
    assert session.exit_code == ExitCode.DAG_FAILED

    captured = capsys.readouterr()
    assert expected_error in captured.out.replace(
        "\n", " "
    ) or expected_error in captured.out.replace("\n", "")


@pytest.mark.end_to_end()
def test_configuration_failed(runner, tmp_path):
    result = runner.invoke(
        cli, ["markers", "-c", tmp_path.joinpath("non_existent_path").as_posix()]
    )
    assert result.exit_code == ExitCode.CONFIGURATION_FAILED


@pytest.mark.end_to_end()
def test_selecting_task_with_keyword_should_run_predecessor(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.produces("first.txt")
    def task_first(produces):
        produces.touch()


    @pytask.mark.depends_on("first.txt")
    def task_second(depends_on):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "-k", "second"])

    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_selecting_task_with_marker_should_run_predecessor(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.produces("first.txt")
    def task_first(produces):
        produces.touch()

    @pytask.mark.wip
    @pytask.mark.depends_on("first.txt")
    def task_second(depends_on):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "-m", "wip"])

    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output
    assert "Warnings" in result.output


@pytest.mark.end_to_end()
def test_selecting_task_with_keyword_ignores_other_task(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("first.txt")
    def task_first():
        pass

    def task_second():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "-k", "second"])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert "1  Skipped" in result.output


@pytest.mark.end_to_end()
def test_selecting_task_with_marker_ignores_other_task(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("first.txt")
    def task_first():
        pass

    @pytask.mark.wip
    def task_second():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "-m", "wip"])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert "1  Skipped" in result.output
    assert "Warnings" in result.output


@pytest.mark.end_to_end()
def test_selecting_task_with_unknown_marker_raises_warning(runner, tmp_path):
    source = """
    import pytask

    @pytask.mark.wip
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "-m", "wip"])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert "Warnings" in result.output


@pytest.mark.end_to_end()
def test_deprecation_warnings_for_decorators(tmp_path):
    source = """
    import pytask

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_write_text(depends_on, produces):
        ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = subprocess.run(
        ("pytest", tmp_path.joinpath("task_module.py").as_posix()),
        capture_output=True,
        check=False,
    )
    assert b"DeprecationWarning: '@pytask.mark.depends_on'" in result.stdout
    assert b"DeprecationWarning: '@pytask.mark.produces'" in result.stdout
