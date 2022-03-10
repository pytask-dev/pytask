from __future__ import annotations

import textwrap

import pytest
from pytask import cli
from pytask import ExitCode
from pytask import main


@pytest.mark.end_to_end
@pytest.mark.parametrize("func_name", ["task_example", "func"])
@pytest.mark.parametrize("task_name", ["the_only_task", None])
def test_task_with_task_decorator(tmp_path, func_name, task_name):
    task_decorator_input = f"{task_name!r}" if task_name else task_name
    source = f"""
    import pytask

    @pytask.mark.task({task_decorator_input})
    @pytask.mark.produces("out.txt")
    def {func_name}(produces):
        produces.write_text("Hello. It's me.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK

    if task_name:
        assert session.tasks[0].name.endswith(f"task_module.py::{task_name}")
    else:
        assert session.tasks[0].name.endswith(f"task_module.py::{func_name}")


@pytest.mark.end_to_end
@pytest.mark.parametrize("func_name", ["task_example", "func"])
@pytest.mark.parametrize("task_name", ["the_only_task", None])
def test_task_with_task_decorator_with_parametrize(tmp_path, func_name, task_name):
    task_decorator_input = f"{task_name!r}" if task_name else task_name
    source = f"""
    import pytask

    @pytask.mark.task({task_decorator_input})
    @pytask.mark.parametrize("produces", ["out_1.txt", "out_2.txt"])
    def {func_name}(produces):
        produces.write_text("Hello. It's me.")
    """
    path_to_module = tmp_path.joinpath("task_module.py")
    path_to_module.write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK

    file_name = path_to_module.name
    if task_name:
        assert session.tasks[0].name.endswith(f"{file_name}::{task_name}[out_1.txt]")
        assert session.tasks[1].name.endswith(f"{file_name}::{task_name}[out_2.txt]")
    else:
        assert session.tasks[0].name.endswith(f"{file_name}::{func_name}[out_1.txt]")
        assert session.tasks[1].name.endswith(f"{file_name}::{func_name}[out_2.txt]")


@pytest.mark.end_to_end
def test_parametrization_in_for_loop(tmp_path, runner):
    source = """
    import pytask

    for i in range(2):

        @pytask.mark.task
        @pytask.mark.produces(f"out_{i}.txt")
        def task_example(produces):
            produces.write_text("Your advertisement could be here.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example[produces0]" in result.output
    assert "task_example[produces1]" in result.output


@pytest.mark.end_to_end
def test_parametrization_in_for_loop_from_markers(tmp_path, runner):
    source = """
    import pytask

    for i in range(2):

        @pytask.mark.task
        @pytask.mark.depends_on(f"in_{i}.txt")
        @pytask.mark.produces(f"out_{i}.txt")
        def example(depends_on, produces):
            produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_0.txt").write_text("Your advertisement could be here.")
    tmp_path.joinpath("in_1.txt").write_text("Or here.")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "example[depends_on0-produces0]" in result.output
    assert "example[depends_on1-produces1]" in result.output


@pytest.mark.end_to_end
def test_parametrization_in_for_loop_from_signature(tmp_path, runner):
    source = """
    import pytask

    for i in range(2):

        @pytask.mark.task
        def example(depends_on=f"in_{i}.txt", produces=f"out_{i}.txt"):
            produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_0.txt").write_text("Your advertisement could be here.")
    tmp_path.joinpath("in_1.txt").write_text("Or here.")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "example[in_0.txt-out_0.txt]" in result.output
    assert "example[in_1.txt-out_1.txt]" in result.output


@pytest.mark.end_to_end
def test_parametrization_in_for_loop_from_markers_and_args(tmp_path, runner):
    source = """
    import pytask

    for i in range(2):

        @pytask.mark.task
        @pytask.mark.produces(f"out_{i}.txt")
        def example(produces, i=i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "example[produces0-0]" in result.output
    assert "example[produces1-1]" in result.output


@pytest.mark.end_to_end
def test_parametrization_in_for_loop_from_decorator(tmp_path, runner):
    source = """
    import pytask

    for i in range(2):

        @pytask.mark.task(name="deco_task", kwargs={"i": i, "produces": f"out_{i}.txt"})
        def example(produces, i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "deco_task[out_0.txt-0]" in result.output
    assert "deco_task[out_1.txt-1]" in result.output


@pytest.mark.end_to_end
def test_parametrization_in_for_loop_with_ids(tmp_path, runner):
    source = """
    import pytask

    for i in range(2):

        @pytask.mark.task(
            "deco_task", id=i, kwargs={"i": i, "produces": f"out_{i}.txt"}
        )
        def example(produces, i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "deco_task[0]" in result.output
    assert "deco_task[1]" in result.output


@pytest.mark.end_to_end
def test_parametrization_in_for_loop_with_error(tmp_path, runner):
    source = """
    import pytask

    for i in range(2):

        @pytask.mark.task
        def task_example(produces=f"out_{i}.txt"):
            raise ValueError
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "2  Failed" in result.output
    assert "Traceback" in result.output
    assert "task_example[out_0.txt]" in result.output
    assert "task_example[out_1.txt]" in result.output


@pytest.mark.end_to_end
def test_parametrization_in_for_loop_from_decorator_w_irregular_dicts(tmp_path, runner):
    source = """
    import pytask

    ID_TO_KWARGS = {
        "first": {"i": 0, "produces": "out_0.txt"},
        "second": {"produces": "out_1.txt"},
    }

    for id_, kwargs in ID_TO_KWARGS.items():

        @pytask.mark.task(name="deco_task", id=id_, kwargs=kwargs)
        def example(produces, i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "deco_task[first]" in result.output
    assert "deco_task[second]" in result.output
    assert "1  Succeeded"
    assert "1  Failed"
    assert "TypeError: example() missing 1 required" in result.output
