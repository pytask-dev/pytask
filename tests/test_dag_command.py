from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from _pytask.dag_command import _RankDirection
from pytask import ExitCode
from pytask import cli

try:
    import pygraphviz  # noqa: F401
except ImportError:  # pragma: no cover
    _IS_PYGRAPHVIZ_INSTALLED = False
else:
    _IS_PYGRAPHVIZ_INSTALLED = True

# Test should run always on remote except on Windows and locally only with the package
# installed.
_TEST_SHOULD_RUN = _IS_PYGRAPHVIZ_INSTALLED or (
    os.environ.get("CI") and sys.platform == "linux"
)
_GRAPH_LAYOUTS = ["dot"]
_TEST_FORMATS = ["dot", "pdf", "png", "jpeg", "svg"]


@pytest.mark.skipif(not _TEST_SHOULD_RUN, reason="pygraphviz is required")
@pytest.mark.parametrize("layout", _GRAPH_LAYOUTS)
@pytest.mark.parametrize("format_", _TEST_FORMATS)
@pytest.mark.parametrize("rankdir", ["LR"])
def test_create_graph_via_cli(tmp_path, runner, format_, layout, rankdir):
    if sys.platform == "win32" and format_ == "pdf":  # pragma: no cover
        pytest.xfail("gvplugin_pango.dll might be missing on Github Actions.")

    source = """
    from pathlib import Path

    def task_example(path=Path("input.txt")): ...
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


@pytest.mark.skipif(not _TEST_SHOULD_RUN, reason="pygraphviz is required")
@pytest.mark.xfail(
    sys.platform == "linux" and sys.version_info[:2] == (3, 9), reason="flakey"
)
@pytest.mark.parametrize("layout", _GRAPH_LAYOUTS)
@pytest.mark.parametrize("format_", _TEST_FORMATS)
@pytest.mark.parametrize("rankdir", [_RankDirection.LR.value, _RankDirection.TB])
def test_create_graph_via_task(tmp_path, format_, layout, rankdir):
    if sys.platform == "win32" and format_ == "pdf":  # pragma: no cover
        pytest.xfail("gvplugin_pango.dll might be missing on Github Actions.")

    rankdir_str = rankdir if isinstance(rankdir, str) else rankdir.name

    source = f"""
    import pytask
    from pathlib import Path
    import networkx as nx

    def task_example(path=Path("input.txt")): ...

    def main():
        dag = pytask.build_dag({{"paths": Path(__file__).parent}})
        dag.graph = {{"rankdir": "{rankdir_str}"}}
        graph = nx.nx_agraph.to_agraph(dag)
        path = Path(__file__).parent.joinpath("dag.{format_}")
        graph.draw(path, prog="{layout}")

    if __name__ == "__main__":
        main()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    result = subprocess.run(
        ("uv", "run", "python", "task_example.py"),
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    assert result.returncode == ExitCode.OK
    assert tmp_path.joinpath(f"dag.{format_}").exists()


def _raise_exc(exc):
    raise exc


def test_raise_error_with_graph_via_cli_missing_optional_dependency(
    monkeypatch, tmp_path, runner
):
    source = """
    from pathlib import Path

    def task_example(path=Path("input.txt")): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    monkeypatch.setattr(
        "_pytask.compat.import_module",
        lambda x: _raise_exc(ImportError("pygraphviz not found")),  # noqa: ARG005
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
        "_pytask.compat.import_module",
        lambda x: _raise_exc(ImportError("pygraphviz not found")),  # noqa: ARG005
    )

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "pytask requires the optional dependency 'pygraphviz'." in result.output
    assert "pip" in result.output
    assert "conda" in result.output
    assert "Traceback" in result.output
    assert not tmp_path.joinpath("dag.png").exists()


def test_raise_error_with_graph_via_cli_missing_optional_program(
    monkeypatch, tmp_path, runner
):
    monkeypatch.setattr(
        "_pytask.compat.import_module",
        lambda x: None,  # noqa: ARG005
    )
    monkeypatch.setattr("_pytask.compat.shutil.which", lambda x: None)  # noqa: ARG005

    source = """
    from pathlib import Path

    def task_example(path=Path("input.txt")): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("input.txt").touch()

    result = runner.invoke(
        cli,
        ["dag", tmp_path.as_posix(), "-o", tmp_path.joinpath("dag.png"), "-l", "dot"],
    )

    assert result.exit_code == ExitCode.FAILED
    assert "pytask requires the optional program 'dot'." in result.output
    assert "conda" in result.output
    assert "Traceback" not in result.output
    assert not tmp_path.joinpath("dag.png").exists()


def test_raise_error_with_graph_via_task_missing_optional_program(
    monkeypatch, tmp_path, runner
):
    monkeypatch.setattr(
        "_pytask.compat.import_module",
        lambda x: None,  # noqa: ARG005
    )
    monkeypatch.setattr("_pytask.compat.shutil.which", lambda x: None)  # noqa: ARG005

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

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "pytask requires the optional program 'dot'." in result.output
    assert "conda" in result.output
    assert "Traceback" in result.output
    assert not tmp_path.joinpath("dag.png").exists()
