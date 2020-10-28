import textwrap

import pytest
from pytask import cli
from pytask import main


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

    session = main({"paths": tmp_path})

    assert session.exit_code == 0
    assert tmp_path.joinpath("out.txt").read_text() == "Here I am. Once again."


@pytest.mark.end_to_end
def test_assert_multiple_dependencies_are_merged_to_dict(tmp_path, runner):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on([(5, "in_5.txt"), (6, "in_6.txt")])
    @pytask.mark.depends_on({3: "in_3.txt", 4: "in_4.txt"})
    @pytask.mark.depends_on(["in_1.txt", "in_2.txt"])
    @pytask.mark.depends_on("in_0.txt")
    @pytask.mark.produces("out.txt")
    def task_dummy(depends_on, produces):
        expected = {
            i: Path(__file__).parent.joinpath(f"in_{i}.txt").resolve()
            for i in range(7)
        }
        assert depends_on == expected
        produces.touch()
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    for name in [f"in_{i}.txt" for i in range(7)]:
        tmp_path.joinpath(name).touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0


@pytest.mark.end_to_end
def test_assert_multiple_products_are_merged_to_dict(tmp_path, runner):
    source = """
    import pytask
    from pathlib import Path

    @pytask.mark.depends_on("in.txt")
    @pytask.mark.produces([(5, "out_5.txt"), (6, "out_6.txt")])
    @pytask.mark.produces({3: "out_3.txt", 4: "out_4.txt"})
    @pytask.mark.produces(["out_1.txt", "out_2.txt"])
    @pytask.mark.produces("out_0.txt")
    def task_dummy(depends_on, produces):
        expected = {
            i: Path(__file__).parent.joinpath(f"out_{i}.txt").resolve()
            for i in range(7)
        }
        assert produces == expected
        for product in produces.values():
            product.touch()
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0
