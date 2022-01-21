import textwrap

from _pytask.nodes import create_task_name
from _pytask.outcomes import ExitCode
from pytask import main


def test_task_with_task_decorator(tmp_path):
    source = """
    import pytask

    @pytask.mark.task("the_only_task")
    @pytask.mark.produces("out.txt")
    def task_example(produces):
        produces.write_text("Hello. It's me.")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == ExitCode.OK
    assert session.tasks[0].name == create_task_name(
        tmp_path.joinpath("task_module.py"), "the_only_task"
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
        tmp_path.joinpath("task_module.py"), "the_parametrized_task[produces0]"
    )
    assert session.tasks[1].name == create_task_name(
        tmp_path.joinpath("task_module.py"), "the_parametrized_task[produces1]"
    )
