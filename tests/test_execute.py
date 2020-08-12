import itertools
import os
import textwrap

import pytest
from pytask import main


@pytest.mark.parametrize(
    "dependencies, products",
    itertools.product(
        ([], ["in.txt"], ["in_1.txt", "in_2.txt"]),
        (["out.txt"], ["out_1.txt", "out_2.txt"]),
    ),
)
def test_execution_w_varying_dependencies_products(tmp_path, dependencies, products):
    source = f"""
    import pytask
    from pathlib import Path


    @pytask.mark.depends_on({dependencies})
    @pytask.mark.produces({products})
    def task_dummy(depends_on, produces):
        if not isinstance(produces, list):
            produces = [produces]
        for product in produces:
            product.touch()
    """
    tmp_path.joinpath("task_dummpy.py").write_text(textwrap.dedent(source))
    for dependency in dependencies:
        tmp_path.joinpath(dependency).touch()

    session = main({"paths": tmp_path})
    assert session.exit_code == 0


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
