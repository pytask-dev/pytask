from __future__ import annotations

import shutil
import sys
import textwrap

import pytest
from _pytask.graph import _RankDirection
from pytask import cli
from pytask import ExitCode

try:
    import pygraphviz  # noqa: F401
except ImportError:  # pragma: no cover
    _IS_PYGRAPHVIZ_INSTALLED = False
else:
    _IS_PYGRAPHVIZ_INSTALLED = True

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


@pytest.mark.end_to_end
@pytest.mark.skipif(not _IS_PYGRAPHVIZ_INSTALLED, reason="pygraphviz is required")
@pytest.mark.parametrize("layout", _PARAMETRIZED_LAYOUTS)
@pytest.mark.parametrize("format_", _TEST_FORMATS)
@pytest.mark.parametrize("rankdir", ["LR"])
def test_create_graph_via_cli(tmp_path, runner, format_, layout, rankdir):
    if sys.platform == "win32" and format_ == "pdf":  # pragma: no cover
        pytest.xfail("gvplugin_pango.dll might be missing on Github Actions.")

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
            "-r",
            rankdir,
        ],
    )

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath(f"dag.{format_}").exists()


@pytest.mark.end_to_end
@pytest.mark.skipif(not _IS_PYGRAPHVIZ_INSTALLED, reason="pygraphviz is required")
@pytest.mark.parametrize("layout", _PARAMETRIZED_LAYOUTS)
@pytest.mark.parametrize("format_", _TEST_FORMATS)
@pytest.mark.parametrize("rankdir", [_RankDirection.LR.value, _RankDirection.TB])
def test_create_graph_via_task(tmp_path, runner, format_, layout, rankdir):
    if sys.platform == "win32" and format_ == "pdf":  # pragma: no cover
        pytest.xfail("gvplugin_pango.dll might be missing on Github Actions.")

    rankdir_str = rankdir if isinstance(rankdir, str) else rankdir.name

    source = f"""
    import pytask
    from pathlib import Path
    import networkx as nx

    @pytask.mark.depends_on("input.txt")
    def task_example(): pass

    def task_create_graph():
        dag = pytask.build_dag({{"paths": Path(__file__).parent}})
        dag.graph = {{"rankdir": "{rankdir_str}"}}
        graph = nx.nx_agraph.to_agraph(dag)
        path = Path(__file__).parent.joinpath("dag.{format_}")
        graph.draw(path, prog="{layout}")
    """

    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath(f"dag.{format_}").exists()


def _raise_exc(exc):
    raise exc


@pytest.mark.end_to_end
def test_raise_error_with_graph_via_cli_missing_optional_dependency(
    monkeypatch, tmp_path, runner
):
    source = """
    import pytask

    @pytask.mark.depends_on("input.txt")
    def task_example(): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    monkeypatch.setattr(
        "_pytask.compat.importlib.import_module",
        lambda x: _raise_exc(ImportError("pygraphviz not found")),  # noqa: U100
    )

    result = runner.invoke(
        cli,
        ["dag", tmp_path.as_posix(), "-o", tmp_path.joinpath("dag.png"), "-l", "dot"],
    )

    assert result.exit_code == ExitCode.FAILED
    assert "pytask requires the optional dependency 'pygraphviz'." in result.output
    assert "pip" in result.output
    assert "conda" in result.output
    assert "Traceback" not in result.output
    assert not tmp_path.joinpath("dag.png").exists()


@pytest.mark.end_to_end
def test_raise_error_with_graph_via_task_missing_optional_dependency(
    monkeypatch, tmp_path, runner
):
    source = """
    import pytask
    from pathlib import Path
    import networkx as nx

    def task_create_graph():
        dag = pytask.build_dag({"paths": Path(__file__).parent})
        graph = nx.nx_agraph.to_agraph(dag)
        path = Path(__file__).parent.joinpath("dag.png")
        graph.draw(path, prog="dot")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    monkeypatch.setattr(
        "_pytask.compat.importlib.import_module",
        lambda x: _raise_exc(ImportError("pygraphviz not found")),  # noqa: U100
    )

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "pytask requires the optional dependency 'pygraphviz'." in result.output
    assert "pip" in result.output
    assert "conda" in result.output
    assert "Traceback" in result.output
    assert not tmp_path.joinpath("dag.png").exists()


@pytest.mark.end_to_end
def test_raise_error_with_graph_via_cli_missing_optional_program(
    monkeypatch, tmp_path, runner
):
    source = """
    import pytask

    @pytask.mark.depends_on("input.txt")
    def task_example(): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    monkeypatch.setattr(
        "_pytask.compat.importlib.import_module", lambda x: None  # noqa: U100
    )
    monkeypatch.setattr("_pytask.compat.shutil.which", lambda x: None)  # noqa: U100

    result = runner.invoke(
        cli,
        ["dag", tmp_path.as_posix(), "-o", tmp_path.joinpath("dag.png"), "-l", "dot"],
    )

    assert result.exit_code == ExitCode.FAILED
    assert "pytask requires the optional program 'dot'." in result.output
    assert "conda" in result.output
    assert "Traceback" not in result.output
    assert not tmp_path.joinpath("dag.png").exists()


@pytest.mark.end_to_end
def test_raise_error_with_graph_via_task_missing_optional_program(
    monkeypatch, tmp_path, runner
):
    source = """
    import pytask
    from pathlib import Path
    import networkx as nx

    def task_create_graph():
        dag = pytask.build_dag({"paths": Path(__file__).parent})
        graph = nx.nx_agraph.to_agraph(dag)
        path = Path(__file__).parent.joinpath("dag.png")
        graph.draw(path, prog="dot")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    monkeypatch.setattr(
        "_pytask.compat.importlib.import_module", lambda x: None  # noqa: U100
    )
    monkeypatch.setattr("_pytask.compat.shutil.which", lambda x: None)  # noqa: U100

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "pytask requires the optional program 'dot'." in result.output
    assert "conda" in result.output
    assert "Traceback" in result.output
    assert not tmp_path.joinpath("dag.png").exists()
