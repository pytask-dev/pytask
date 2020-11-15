import os
import textwrap

import pytest
from _pytask.exceptions import NodeNotFoundError
from pytask import main


@pytest.mark.end_to_end
def test_node_not_found_in_task_setup(tmp_path):
    """Test for :class:`_pytask.exceptions.NodeNotFoundError` in task setup.

    Before a task is executed, pytask checks whether all dependencies can be found.
    Normally, missing dependencies are caught during resolving dependencies if they are
    root nodes or when a task does not produce a node.

    To force this error one task accidentally deletes the product of another task.

    """
    source = """
    import pytask

    @pytask.mark.produces(["out_1.txt", "deleted.txt"])
    def task_1(produces):
        for product in produces.values():
            product.touch()

    @pytask.mark.depends_on("out_1.txt")
    @pytask.mark.produces("out_2.txt")
    def task_2(depends_on, produces):
        depends_on.with_name("deleted.txt").unlink()
        produces.touch()

    @pytask.mark.depends_on(["deleted.txt", "out_2.txt"])
    def task_3(depends_on):
        pass

    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))

    session = main({"paths": tmp_path})

    assert session.exit_code == 1
    assert sum(i.success for i in session.execution_reports) == 2

    report = session.execution_reports[2]
    assert isinstance(report.exc_info[1], NodeNotFoundError)


@pytest.mark.end_to_end
@pytest.mark.parametrize(
    "dependencies",
    [[], ["in.txt"], ["in_1.txt", "in_2.txt"]],
)
@pytest.mark.parametrize("products", [["out.txt"], ["out_1.txt", "out_2.txt"]])
def test_execution_w_varying_dependencies_products(tmp_path, dependencies, products):
    source = f"""
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on({dependencies})
    @pytask.mark.produces({products})
    def task_dummy(depends_on, produces):
        if isinstance(produces, dict):
            produces = produces.values()
        elif isinstance(produces, Path):
            produces = [produces]
        for product in produces:
            product.touch()
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    for dependency in dependencies:
        tmp_path.joinpath(dependency).touch()

    session = main({"paths": tmp_path})
    assert session.exit_code == 0


@pytest.mark.end_to_end
def test_depends_on_and_produces_can_be_used_in_task(tmp_path):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(depends_on, produces):
        assert isinstance(depends_on, Path) and isinstance(produces, Path)
        produces.write_text(depends_on.read_text())
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Here I am. Once again.")

    os.chdir(tmp_path)
    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert tmp_path.joinpath("out.txt").read_text() == "Here I am. Once again."
