from __future__ import annotations

import textwrap

import pytest
from _pytask.nodes import create_task_name
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
        assert session.tasks[0].name == create_task_name(
            tmp_path.joinpath("task_module.py"), task_name
        )
    else:
        assert session.tasks[0].name == create_task_name(
            tmp_path.joinpath("task_module.py"), func_name
        )


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
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK

    if task_name:
        assert session.tasks[0].name == create_task_name(
            tmp_path.joinpath("task_module.py"), f"{task_name}[out_1.txt]"
        )
        assert session.tasks[1].name == create_task_name(
            tmp_path.joinpath("task_module.py"), f"{task_name}[out_2.txt]"
        )
    else:
        assert session.tasks[0].name == create_task_name(
            tmp_path.joinpath("task_module.py"), f"{func_name}[out_1.txt]"
        )
        assert session.tasks[1].name == create_task_name(
            tmp_path.joinpath("task_module.py"), f"{func_name}[out_2.txt]"
        )
