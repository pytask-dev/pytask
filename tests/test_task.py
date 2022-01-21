import textwrap

import pytest
from _pytask.nodes import create_task_name
from _pytask.outcomes import ExitCode
from pytask import main


@pytest.mark.parametrize("task_name", ["'the_only_task'", None])
def test_task_with_task_decorator(tmp_path, task_name):
    source = f"""
    import pytask

    @pytask.mark.task({task_name})
    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.write_text("Hello. It's me.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    if task_name:
        assert session.tasks[0].name == create_task_name(
            tmp_path.joinpath("task_module.py"), "the_only_task"
        )
    else:
        assert session.tasks[0].name == create_task_name(
            tmp_path.joinpath("task_module.py"), "task_example"
        )


def test_task_with_task_decorator_with_parametrize(tmp_path):
    source = """
    import pytask

    @pytask.mark.task("the_parametrized_task")
    @pytask.mark.parametrize("produces", ["out_1.txt", "out_2.txt"])
    def task_example(produces):
        produces.write_text("Hello. It's me.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    assert session.tasks[0].name == create_task_name(
        tmp_path.joinpath("task_module.py"), "the_parametrized_task[out_1.txt]"
    )
    assert session.tasks[1].name == create_task_name(
        tmp_path.joinpath("task_module.py"), "the_parametrized_task[out_2.txt]"
    )
