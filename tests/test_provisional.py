from __future__ import annotations

import textwrap

import pytest
from pytask import ExitCode
from pytask import TaskOutcome
from pytask import build
from pytask import cli


@pytest.mark.end_to_end()
def test_task_that_produces_provisional_path_node(tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode, Product
    from pathlib import Path

    def task_example(
        root_path: Annotated[Path, DirectoryNode(pattern="*.txt"), Product]
    ):
        root_path.joinpath("a.txt").write_text("Hello, ")
        root_path.joinpath("b.txt").write_text("World!")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    assert len(session.tasks[0].produces["root_path"]) == 2

    # Rexecution does skip the task.
    session = build(paths=tmp_path)
    assert session.execution_reports[0].outcome == TaskOutcome.SKIP_UNCHANGED


@pytest.mark.end_to_end()
def test_task_that_depends_on_relative_provisional_path_node(tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode
    from pathlib import Path

    def task_example(
        paths = DirectoryNode(pattern="[ab].txt")
    ) -> Annotated[str, Path("merged.txt")]:
        path_dict = {path.stem: path for path in paths}
        return path_dict["a"].read_text() + path_dict["b"].read_text()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("a.txt").write_text("Hello, ")
    tmp_path.joinpath("b.txt").write_text("World!")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    assert len(session.tasks[0].depends_on["paths"]) == 2


@pytest.mark.end_to_end()
def test_task_that_depends_on_provisional_path_node_with_absolute_root_dir(tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode
    from pathlib import Path

    root_dir = Path(__file__).parent / "subfolder"

    def task_example(
        paths = DirectoryNode(root_dir=root_dir, pattern="[ab].txt")
    ) -> Annotated[str, Path(__file__).parent.joinpath("merged.txt")]:
        path_dict = {path.stem: path for path in paths}
        return path_dict["a"].read_text() + path_dict["b"].read_text()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("subfolder").mkdir()
    tmp_path.joinpath("subfolder", "a.txt").write_text("Hello, ")
    tmp_path.joinpath("subfolder", "b.txt").write_text("World!")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    assert len(session.tasks[0].depends_on["paths"]) == 2


@pytest.mark.end_to_end()
def test_task_that_depends_on_provisional_path_node_with_relative_root_dir(tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode
    from pathlib import Path

    def task_example(
        paths = DirectoryNode(root_dir=Path("subfolder"), pattern="[ab].txt")
    ) -> Annotated[str, Path(__file__).parent.joinpath("merged.txt")]:
        path_dict = {path.stem: path for path in paths}
        return path_dict["a"].read_text() + path_dict["b"].read_text()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("subfolder").mkdir()
    tmp_path.joinpath("subfolder", "a.txt").write_text("Hello, ")
    tmp_path.joinpath("subfolder", "b.txt").write_text("World!")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    assert len(session.tasks[0].depends_on["paths"]) == 2


@pytest.mark.end_to_end()
def test_task_that_depends_on_provisional_task(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode, task
    from pathlib import Path

    def task_produces() -> Annotated[None, DirectoryNode(pattern="[ab].txt")]:
        path = Path(__file__).parent
        path.joinpath("a.txt").write_text("Hello, ")
        path.joinpath("b.txt").write_text("World!")

    @task(after=task_produces)
    def task_depends(
        paths = DirectoryNode(pattern="[ab].txt")
    ) -> Annotated[str, Path(__file__).parent.joinpath("merged.txt")]:
        path_dict = {path.stem: path for path in paths}
        return path_dict["a"].read_text() + path_dict["b"].read_text()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "2  Collected tasks" in result.output
    assert "2  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_gracefully_fail_when_dag_raises_error(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode, task
    from pathlib import Path

    def task_produces() -> Annotated[None, DirectoryNode(pattern="*.txt")]:
        path = Path(__file__).parent
        path.joinpath("a.txt").write_text("Hello, ")
        path.joinpath("b.txt").write_text("World!")

    @task(after=task_produces)
    def task_depends(
        paths = DirectoryNode(pattern="[ab].txt")
    ) -> Annotated[str, Path(__file__).parent.joinpath("merged.txt")]:
        path_dict = {path.stem: path for path in paths}
        return path_dict["a"].read_text() + path_dict["b"].read_text()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
    assert "There are some tasks which produce" in result.output


@pytest.mark.end_to_end()
def test_provisional_task_generation(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode, task
    from pathlib import Path

    def task_produces() -> Annotated[None, DirectoryNode(pattern="[ab].txt")]:
        path = Path(__file__).parent
        path.joinpath("a.txt").write_text("Hello, ")
        path.joinpath("b.txt").write_text("World!")

    @task(after=task_produces, is_generator=True)
    def task_depends(
        paths = DirectoryNode(pattern="[ab].txt")
    ):
        for path in paths:

            @task
            def task_copy(
                path: Path = path
            ) -> Annotated[str, path.with_name(path.stem + "-copy.txt")]:
                return path.read_text()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "4  Collected tasks" in result.output
    assert "4  Succeeded" in result.output
    assert tmp_path.joinpath("a-copy.txt").exists()
    assert tmp_path.joinpath("b-copy.txt").exists()


@pytest.mark.end_to_end()
def test_gracefully_fail_when_task_generator_raises_error(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode, task, Product
    from pathlib import Path

    @task(is_generator=True)
    def task_example(
        root_dir: Annotated[Path, DirectoryNode(pattern="[a].txt"), Product]
    ) -> ...:
        raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
    assert "1  Collected task" in result.output
    assert "1  Failed" in result.output


@pytest.mark.end_to_end()
def test_use_provisional_node_as_product_in_generator_without_rerun(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode, task, Product
    from pathlib import Path

    @task(is_generator=True)
    def task_example(
        root_dir: Annotated[Path, DirectoryNode(pattern="[ab].txt"), Product]
    ) -> ...:
        for path in (root_dir / "a.txt", root_dir / "b.txt"):

            @task
            def create_file() -> Annotated[Path, path]:
                return "content"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "3  Collected task" in result.output
    assert "3  Succeeded" in result.output

    # No rerun.
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "3  Collected task" in result.output
    assert "1  Succeeded" in result.output
    assert "2  Skipped because unchanged" in result.output


def test_provisional_nodes_are_resolved_before_persist(runner, tmp_path):
    source = """
    from pytask import DirectoryNode, mark
    from pathlib import Path

    @mark.persist
    def task_example(path = DirectoryNode(root_dir=Path("files"), pattern="*.py")): ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("files").mkdir()
    tmp_path.joinpath("files", "a.py").write_text("a = 1")

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
def test_root_dir_is_created(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import DirectoryNode, Product
    from pathlib import Path

    def task_example(
        root_path: Annotated[
            Path, DirectoryNode(root_dir=Path("subfolder"), pattern="*.txt"), Product
        ]
    ):
        root_path.joinpath("a.txt").write_text("Hello, ")
        root_path.joinpath("b.txt").write_text("World!")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("subfolder", "a.txt").exists()
    assert tmp_path.joinpath("subfolder", "b.txt").exists()
