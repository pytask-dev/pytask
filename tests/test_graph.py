import shutil
import textwrap

import pytest
from pytask import cli

try:
    import pydot  # noqa: F401
except ImportError:
    _IS_PYDOT_INSTALLED = False
else:
    _IS_PYDOT_INSTALLED = True

_GRAPH_LAYOUTS = ["neato", "dot", "fdp", "sfdp", "twopi", "circo"]


_PARAMETRIZED_LAYOUTS = [
    pytest.param(
        layout,
        marks=pytest.mark.skip(reason=f"{layout} not available")
        if shutil.which(layout) is None
        else [],
    )
    for layout in _GRAPH_LAYOUTS
]


_TEST_FORMATS = ["dot", "pdf", "png", "jpeg", "svg"]


@pytest.mark.skipif(not _IS_PYDOT_INSTALLED, reason="pydot is required")
@pytest.mark.parametrize("layout", _PARAMETRIZED_LAYOUTS)
@pytest.mark.parametrize("format_", _TEST_FORMATS)
def test_create_graph_via_cli(tmp_path, runner, format_, layout):
    source = """
    import pytask

    @pytask.mark.depends_on("input.txt")
    def task_example(): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    result = runner.invoke(
        cli,
        [
            "dag",
            tmp_path.as_posix(),
            "-o",
            tmp_path.joinpath(f"dag.{format_}"),
            "-l",
            layout,
        ],
    )

    assert result.exit_code == 0
    assert tmp_path.joinpath(f"dag.{format_}").exists()


@pytest.mark.skipif(not _IS_PYDOT_INSTALLED, reason="pydot is required")
@pytest.mark.parametrize("layout", _PARAMETRIZED_LAYOUTS)
@pytest.mark.parametrize("format_", _TEST_FORMATS)
def test_create_graph_via_task(tmp_path, runner, format_, layout):
    source = f"""
    import pytask
    from pathlib import Path
    import networkx as nx

    @pytask.mark.depends_on("input.txt")
    def task_example(): pass

    def task_create_graph():
        dag = pytask.build_dag({{"paths": Path(__file__).parent}})
        graph = nx.nx_pydot.to_pydot(dag)
        path = Path(__file__).parent.joinpath("dag.{format_}")
        graph.write(path, prog="{layout}", format=path.suffix[1:])
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == 0
    assert tmp_path.joinpath(f"dag.{format_}").exists()
