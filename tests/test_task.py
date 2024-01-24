from __future__ import annotations

import textwrap

import pytest
from pytask import build
from pytask import cli
from pytask import ExitCode


@pytest.mark.end_to_end()
@pytest.mark.parametrize("func_name", ["task_example", "func"])
@pytest.mark.parametrize("task_name", ["the_only_task", None])
def test_task_with_task_decorator(tmp_path, func_name, task_name):
    task_decorator_input = f"{task_name!r}" if task_name else task_name
    source = f"""
    from pytask import task
    from pathlib import Path

    @task({task_decorator_input})
    def {func_name}(produces=Path("out.txt")):
        produces.write_text("Hello. It's me.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK

    if task_name:
        assert session.tasks[0].name.endswith(f"task_module.py::{task_name}")
    else:
        assert session.tasks[0].name.endswith(f"task_module.py::{func_name}")


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task
        def task_example(produces=Path(f"out_{i}.txt")):
            produces.write_text("Your advertisement could be here.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example[produces0]" in result.output
    assert "task_example[produces1]" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_from_markers(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task
        def example(path=Path(f"in_{i}.txt"), produces=Path(f"out_{i}.txt")):
            produces.write_text(path.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_0.txt").write_text("Your advertisement could be here.")
    tmp_path.joinpath("in_1.txt").write_text("Or here.")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "example[path0-produces0]" in result.output
    assert "example[path1-produces1]" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_from_signature(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task
        def example(path=Path(f"in_{i}.txt"), produces=Path(f"out_{i}.txt")):
            produces.write_text(path.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in_0.txt").write_text("Your advertisement could be here.")
    tmp_path.joinpath("in_1.txt").write_text("Or here.")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "example[path0-produces0]" in result.output
    assert "example[path1-produces1]" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_from_markers_and_args(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task
        def example(produces=Path(f"out_{i}.txt"), i=i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "example[produces0-0]" in result.output
    assert "example[produces1-1]" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_from_decorator(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task(name="deco_task", kwargs={"i": i, "produces": Path(f"out_{i}.txt")})
        def example(produces, i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "deco_task[produces0-0]" in result.output
    assert "deco_task[produces1-1]" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_with_ids(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task("deco_task", id=str(i), kwargs={"i": i, "produces": Path(f"out_{i}.txt")})
        def example(produces, i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "deco_task[0]" in result.output
    assert "deco_task[1]" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_with_error(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task
        def task_example(produces=Path(f"out_{i}.txt")):
            raise ValueError
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "2  Failed" in result.output
    assert "Traceback" in result.output
    assert "task_example[produces0]" in result.output
    assert "task_example[produces1]" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_from_decorator_w_irregular_dicts(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    ID_TO_KWARGS = {
        "first": {"i": 0, "produces": Path("out_0.txt")},
        "second": {"produces": Path("out_1.txt")},
    }

    for id_, kwargs in ID_TO_KWARGS.items():

        @task(name="deco_task", id=id_, kwargs=kwargs)
        def example(produces, i):
            produces.write_text(str(i))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "deco_task[first]" in result.output
    assert "deco_task[second]" in result.output
    assert "1  Succeeded" in result.output
    assert "1  Failed" in result.output
    assert "TypeError: example() missing 1 required" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_with_one_iteration(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(1):

        @task
        def task_example(produces=Path(f"out_{i}.txt")):
            produces.write_text("Your advertisement could be here.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example " in result.output
    assert "Collected 1 task" in result.output


@pytest.mark.end_to_end()
def test_parametrization_in_for_loop_and_normal(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(1):

        @task
        def task_example(produces=Path(f"out_{i}.txt")):
            produces.write_text("Your advertisement could be here.")

    @task
    def task_example(produces=Path(f"out_1.txt")):
        produces.write_text("Your advertisement could be here.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example[produces0]" in result.output
    assert "task_example[produces1]" in result.output
    assert "Collected 2 tasks" in result.output


@pytest.mark.end_to_end()
def test_parametrized_names_without_parametrization(tmp_path, runner):
    source = """
    from pytask import task
    from pathlib import Path

    for i in range(2):

        @task
        def task_example(produces=Path(f"out_{i}.txt")):
            produces.write_text("Your advertisement could be here.")

    @task
    def task_example(produces=Path("out_2.txt")):
        produces.write_text("Your advertisement could be here.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example[produces0]" in result.output
    assert "task_example[produces1]" in result.output
    assert "task_example[produces2]" in result.output
    assert "Collected 3 tasks" in result.output


@pytest.mark.end_to_end()
def test_order_of_decorator_does_not_matter(tmp_path, runner):
    source = """
    from pytask import task, mark
    from pathlib import Path

    @task
    @mark.skip
    def task_example(produces=Path(f"out.txt")):
        produces.write_text("Your advertisement could be here.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Skipped" in result.output


@pytest.mark.end_to_end()
def test_task_function_with_partialed_args(tmp_path, runner):
    source = """
    import functools
    from pathlib import Path

    def func(produces, content):
        produces.write_text(content)

    task_func = functools.partial(func, content="hello", produces=Path("out.txt"))
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task." in result.output
    assert "1  Succeeded" in result.output
    assert tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end()
def test_task_function_with_partialed_args_and_task_decorator(tmp_path, runner):
    source = """
    from pytask import task
    import functools
    from pathlib import Path

    def func(content):
        return content

    task_func = task(produces=Path("out.txt"))(
        functools.partial(func, content="hello")
    )
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert tmp_path.joinpath("out.txt").read_text() == "hello"


@pytest.mark.end_to_end()
def test_parametrized_tasks_without_arguments_in_signature(tmp_path, runner):
    """This happens when plugins replace the function with its own implementation.

    Then, there is usually no point in adding arguments to the function signature. Or
    when people build weird workarounds like the one below.

    """
    source = f"""
    from pytask import task
    from pathlib import Path

    for i in range(1):

        @task
        def task_example(produces=Path(f"out_{{i}}.txt")):
            Path("{tmp_path.as_posix()}").joinpath(f"out_{{i}}.txt").write_text(
                "I use globals. How funny."
            )


    @task
    def task_example(produces=Path("out_1.txt")):
        Path("{tmp_path.as_posix()}").joinpath("out_1.txt").write_text(
            "I use globals. How funny."
        )

    @task(id="hello")
    def task_example(produces=Path("out_2.txt")):
        Path("{tmp_path.as_posix()}").joinpath("out_2.txt").write_text(
            "I use globals. How funny."
        )
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example[produces0]" in result.output
    assert "task_example[produces1]" in result.output
    assert "task_example[hello]" in result.output
    assert "Collected 3 tasks" in result.output


@pytest.mark.end_to_end()
def test_that_dynamically_creates_tasks_are_captured(runner, tmp_path):
    source = """
    from pytask import task

    _DEFINITION = '''
    @task
    def task_example():
        pass
    '''

    for i in range(2):
        exec(_DEFINITION)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example[0]" in result.output
    assert "task_example[1]" in result.output
    assert "Collected 2 tasks" in result.output


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    "irregular_id", [1, (1,), [1], {1}, ["a"], list("abc"), ((1,), (2,)), ({0}, {1})]
)
def test_raise_errors_for_irregular_ids(runner, tmp_path, irregular_id):
    source = f"""
    from pytask import task

    @task(id={irregular_id})
    def task_example():
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Argument 'id' of @task" in result.output


@pytest.mark.end_to_end()
def test_raise_error_if_parametrization_produces_non_unique_tasks(tmp_path):
    source = """
    from pytask import task

    for i in [0, 0]:
        @task(id=str(i))
        def task_func(i=i):
            pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.COLLECTION_FAILED
    assert isinstance(session.collection_reports[0].exc_info[1], ValueError)


@pytest.mark.end_to_end()
def test_task_receives_unknown_kwarg(runner, tmp_path):
    source = """
    from pytask import task

    @task(kwargs={"i": 1})
    def task_example(): pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED


@pytest.mark.end_to_end()
def test_task_receives_namedtuple(runner, tmp_path):
    source = """
    from typing_extensions import NamedTuple, Annotated
    from pathlib import Path
    from pytask import Product, PythonNode, task

    class Args(NamedTuple):
        path_in: Path
        arg: str
        path_out: Path

    args = Args(Path("input.txt"), "world!", Path("output.txt"))

    @task(kwargs=args)
    def task_example(
        path_in: Path, arg: str, path_out: Annotated[Path, Product]
    ) -> None:
        path_out.write_text(path_in.read_text() + " " + arg)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").write_text("Hello")

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("output.txt").read_text() == "Hello world!"


@pytest.mark.end_to_end()
def test_task_kwargs_overwrite_default_arguments(runner, tmp_path):
    source = """
    from pytask import Product, task
    from pathlib import Path
    from typing_extensions import Annotated

    @task(kwargs={
        "in_path": Path("in.txt"), "addition": "world!", "out_path": Path("out.txt")
    })
    def task_example(
        in_path: Path = Path("not_used_in.txt"),
        addition: str = "planet!",
        out_path: Annotated[Path, Product] = Path("not_used_out.txt"),
    ) -> None:
        out_path.write_text(in_path.read_text() + addition)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Hello ")

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").read_text() == "Hello world!"
    assert not tmp_path.joinpath("not_used_out.txt").exists()


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    "node_def", ["PathNode(path=Path('file.txt'))", "Path('file.txt')"]
)
def test_return_with_task_decorator(runner, tmp_path, node_def):
    source = f"""
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import task, PathNode

    @task(produces={node_def})
    def task_example():
        return "Hello, World!"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file.txt").read_text() == "Hello, World!"


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    "node_def",
    [
        "(PathNode(path=Path('file1.txt')), PathNode(path=Path('file2.txt')))",
        "(Path('file1.txt'), Path('file2.txt'))",
    ],
)
def test_return_with_tuple_and_task_decorator(runner, tmp_path, node_def):
    source = f"""
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import task, PathNode

    @task(produces={node_def})
    def task_example():
        return "Hello,", "World!"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file1.txt").read_text() == "Hello,"
    assert tmp_path.joinpath("file2.txt").read_text() == "World!"


def test_error_when_function_is_defined_outside_loop_body(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import task, Product

    def func(path: Annotated[Path, Product]):
        path.touch()

    for path in (Path("a.txt"), Path("b.txt")):
        task(kwargs={"path": path})(func)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Duplicated tasks" in result.output
    assert "id=None" in result.output


def test_error_when_function_is_defined_outside_loop_body_with_id(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import task
    from pytask import Product

    def func(path: Annotated[Path, Product]):
        path.touch()

    for path in (Path("a.txt"), Path("b.txt")):
        task(kwargs={"path": path}, id=path.name)(func)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Duplicated tasks" in result.output
    assert "id=b.txt" in result.output


def test_task_will_be_executed_after_another_one_with_string(runner, tmp_path):
    source = """
    from pytask import task
    from pathlib import Path
    from typing_extensions import Annotated

    @task(after="task_first")
    def task_second():
        assert Path(__file__).parent.joinpath("out.txt").exists()

    def task_first() -> Annotated[str, Path("out.txt")]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output

    # Make sure that the dependence does not only apply to the task (and task module),
    # but also it products.
    tmp_path.joinpath("out.txt").write_text("Hello, Moon!")
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert "1  Skipped because unchanged" in result.output


def test_task_will_be_executed_after_another_one_with_function(tmp_path):
    source = """
    from pytask import task
    from pathlib import Path
    from typing_extensions import Annotated

    def task_first() -> Annotated[str, Path("out.txt")]:
        return "Hello, World!"

    @task(after=task_first)
    def task_second():
        assert Path(__file__).parent.joinpath("out.txt").exists()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    assert session.exit_code == ExitCode.OK


def test_raise_error_for_wrong_after_expression(runner, tmp_path):
    source = """
    from pytask import task
    from pathlib import Path
    from typing_extensions import Annotated

    @task(after="(")
    def task_example() -> Annotated[str, Path("out.txt")]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.DAG_FAILED
    assert "Wrong expression passed to 'after'" in result.output


def test_raise_error_with_builtin_function_as_task(runner, tmp_path):
    source = """
    from pytask import task
    from pathlib import Path
    from datetime import datetime

    task(
        kwargs={"format": "%y/%m/%d"}, produces=Path("time.txt")
    )(datetime.utcnow().strftime)
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Builtin functions cannot be wrapped" in result.output


def test_task_function_in_another_module(runner, tmp_path):
    source = """
    def func():
        return "Hello, World!"
    """
    tmp_path.joinpath("module.py").write_text(textwrap.dedent(source))

    source = """
    from pytask import task
    from pathlib import Path
    from pytask.path import import_path
    import inspect

    _ROOT_PATH = Path(__file__).parent

    module = import_path(_ROOT_PATH / "module.py", _ROOT_PATH)
    name_to_obj = dict(inspect.getmembers(module))

    task(produces=Path("out.txt"))(name_to_obj["func"])
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "1  Failed" in result.output
