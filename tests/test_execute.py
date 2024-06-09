from __future__ import annotations

import json
import pickle
import re
import subprocess
import sys
import textwrap

import pytask
import pytest
from pytask import CaptureMethod
from pytask import ExitCode
from pytask import NodeNotFoundError
from pytask import PathNode
from pytask import TaskOutcome
from pytask import TaskWithoutPath
from pytask import build
from pytask import cli

from tests.conftest import enter_directory


@pytest.mark.xfail(sys.platform == "win32", reason="See #293.")
@pytest.mark.end_to_end()
def test_python_m_pytask(tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    subprocess.run(["python", "-m", "pytask", tmp_path.as_posix()], check=False)


@pytest.mark.end_to_end()
def test_execute_w_autocollect(runner, tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    with enter_directory(tmp_path):
        result = runner.invoke(cli)
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_task_did_not_produce_node(tmp_path):
    source = """
    from pathlib import Path

    def task_example(produces=Path("out.txt")): ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.FAILED
    assert len(session.execution_reports) == 1
    assert isinstance(session.execution_reports[0].exc_info[1], NodeNotFoundError)


@pytest.mark.end_to_end()
def test_task_did_not_produce_multiple_nodes_and_all_are_shown(runner, tmp_path):
    source = """
    from pathlib import Path

    def task_example(produces=[Path("1.txt"), Path("2.txt")]): ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "NodeNotFoundError" in result.output
    assert "1.txt" in result.output
    assert "2.txt" in result.output


@pytest.mark.end_to_end()
def test_missing_product(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import Product

    def task_with_non_path_dependency(path: Annotated[Path, Product]): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED


@pytest.mark.end_to_end()
def test_node_not_found_in_task_setup(tmp_path):
    """Test for :class:`_pytask.exceptions.NodeNotFoundError` in task setup.

    Before a task is executed, pytask checks whether all dependencies can be found.
    Normally, missing dependencies are caught during resolving dependencies if they are
    root nodes or when a task does not produce a node.

    To force this error one task accidentally deletes the product of another task.

    """
    source = """
    import pytask
    from typing_extensions import Annotated
    from pathlib import Path

    def task_1() -> Annotated[None, (Path("out_1.txt"), Path("deleted.txt"))]:
        return "", ""

    def task_2(path = Path("out_1.txt")) -> Annotated[str, Path("out_2.txt")]:
        path.with_name("deleted.txt").unlink()
        return ""

    def task_3(paths = [Path("deleted.txt"), Path("out_2.txt")]):
        ...
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.FAILED
    assert sum(i.outcome == TaskOutcome.SUCCESS for i in session.execution_reports) == 2

    report = session.execution_reports[2]
    assert report.outcome == TaskOutcome.FAIL
    assert isinstance(report.exc_info[1], NodeNotFoundError)


@pytest.mark.end_to_end()
def test_depends_on_and_produces_can_be_used_in_task(tmp_path):
    source = """
    from pathlib import Path

    def task_example(path=Path("in.txt"), produces=Path("out.txt")):
        assert isinstance(path, Path) and isinstance(produces, Path)
        produces.write_text(path.read_text())
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("Here I am. Once again.")

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").read_text() == "Here I am. Once again."


@pytest.mark.end_to_end()
@pytest.mark.parametrize("n_failures", [1, 2, 3])
def test_execution_stops_after_n_failures(tmp_path, n_failures):
    source = """
    def task_1(): raise Exception
    def task_2(): raise Exception
    def task_3(): raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path, max_failures=n_failures)

    assert len(session.tasks) == 3
    assert len(session.execution_reports) == n_failures


@pytest.mark.end_to_end()
@pytest.mark.parametrize("stop_after_first_failure", [False, True])
def test_execution_stop_after_first_failure(tmp_path, stop_after_first_failure):
    source = """
    def task_1(): raise Exception
    def task_2(): raise Exception
    def task_3(): raise Exception
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path, stop_after_first_failure=stop_after_first_failure)

    assert len(session.tasks) == 3
    assert len(session.execution_reports) == 1 if stop_after_first_failure else 3


@pytest.mark.end_to_end()
def test_scheduling_w_priorities(tmp_path):
    source = """
    import pytask

    @pytask.mark.try_first
    def task_z(): pass

    def task_x(): pass

    @pytask.mark.try_last
    def task_y(): pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert session.execution_reports[0].task.name.endswith("task_z")
    assert session.execution_reports[1].task.name.endswith("task_x")
    assert session.execution_reports[2].task.name.endswith("task_y")


@pytest.mark.end_to_end()
@pytest.mark.parametrize("show_errors_immediately", [True, False])
def test_show_errors_immediately(runner, tmp_path, show_errors_immediately):
    source = """
    def task_succeed(): pass
    def task_error(): raise ValueError
    """
    tmp_path.joinpath("task_error.py").write_text(textwrap.dedent(source))

    args = [tmp_path.as_posix()]
    if show_errors_immediately:
        args.append("--show-errors-immediately")
    result = runner.invoke(cli, args)

    assert result.exit_code == ExitCode.FAILED
    assert "::task_succeed │ ." in result.output

    matches_traceback = re.findall("Traceback", result.output)
    if show_errors_immediately:
        assert len(matches_traceback) == 2
    else:
        assert len(matches_traceback) == 1


@pytest.mark.end_to_end()
@pytest.mark.parametrize("verbose", [1, 2])
def test_traceback_of_previous_task_failed_is_not_shown(runner, tmp_path, verbose):
    source = """
    from pathlib import Path

    def task_first(produces=Path("in.txt")): raise ValueError

    def task_second(path=Path("in.txt")): ...
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix(), "--verbose", str(verbose)])

    assert result.exit_code == ExitCode.FAILED
    assert ("Task task_example.py::task_second failed" in result.output) is (
        verbose == 2
    )


@pytest.mark.end_to_end()
def test_that_dynamically_creates_tasks_are_captured(runner, tmp_path):
    source = """
    _DEFINITION = '''
    def task_example():
        pass
    '''

    exec(_DEFINITION)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "task_example" in result.output
    assert "Collected 1 task" in result.output


@pytest.mark.end_to_end()
def test_task_executed_with_force_although_unchanged(tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    session = build(paths=tmp_path)
    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS
    session = build(paths=tmp_path, force=True)
    assert session.execution_reports[0].outcome == TaskOutcome.SUCCESS


@pytest.mark.end_to_end()
def test_task_executed_with_force_although_unchanged_runner(runner, tmp_path):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "Collected 1 task" in result.output
    assert "1  Succeeded" in result.output

    result = runner.invoke(cli, [tmp_path.as_posix(), "--force"])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_task_is_not_reexecuted_when_modification_changed_file_not(runner, tmp_path):
    tmp_path.joinpath("task_example.py").write_text("def task_example(): pass")
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output

    tmp_path.joinpath("task_example.py").write_text("def task_example(): pass")
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Skipped" in result.output


@pytest.mark.end_to_end()
@pytest.mark.parametrize("arg_name", ["path", "produces"])
def test_task_with_product_annotation(tmp_path, arg_name):
    """Using 'produces' with a product annotation should not cause an error."""
    source = f"""
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import Product

    def task_example({arg_name}: Annotated[Path, Product] = Path("out.txt")) -> None:
        {arg_name}.touch()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path, capture=CaptureMethod.NO)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 1
    task = session.tasks[0]
    assert arg_name in task.produces


@pytest.mark.end_to_end()
def test_task_errors_with_nested_product_annotation(tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated, Dict
    from pytask import Product

    def task_example(
        paths_to_file: Dict[str, Annotated[Path, Product]] = {"a": Path("out.txt")}
    ) -> None:
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path, capture=CaptureMethod.NO)

    assert session.exit_code == ExitCode.FAILED
    assert len(session.tasks) == 1
    task = session.tasks[0]
    assert "paths_to_file" not in task.produces


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    "definition",
    [
        " = PythonNode(value=data['dependency'], hash=True)",
        ": Annotated[Any, PythonNode(value=data['dependency'], hash=True)]",
    ],
)
def test_task_with_hashed_python_node(runner, tmp_path, definition):
    source = f"""
    import json
    from pathlib import Path
    from pytask import Product, PythonNode
    from typing_extensions import Annotated, Any

    data = json.loads(Path(__file__).parent.joinpath("data.json").read_text())

    def task_example(
        dependency{definition},
        path: Annotated[Path, Product] = Path("out.txt")
    ) -> None:
        path.write_text(dependency)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("data.json").write_text('{"dependency": "hello"}')

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").read_text() == "hello"

    tmp_path.joinpath("data.json").write_text('{"dependency": "world"}')

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").read_text() == "world"


@pytest.mark.end_to_end()
def test_return_with_path_annotation_as_return(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated

    def task_example() -> Annotated[str, Path("file.txt")]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file.txt").read_text() == "Hello, World!"


@pytest.mark.end_to_end()
def test_return_with_pathnode_annotation_as_return(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import PathNode

    def task_example() -> Annotated[str, PathNode(path=Path("file.txt"))]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file.txt").read_text() == "Hello, World!"


@pytest.mark.end_to_end()
@pytest.mark.parametrize(
    ("product_def", "return_def"),
    [
        ("produces=PickleNode(path=Path('data.pkl')))", "produces.save(1)"),
        (
            "node: Annotated[PickleNode, PickleNode(path=Path('data.pkl')), Product])",
            "node.save(1)",
        ),
        (") -> Annotated[int, PickleNode(path=Path('data.pkl'))]", "return 1"),
    ],
)
def test_custom_node_as_product(runner, tmp_path, product_def, return_def):
    source = f"""
    from __future__ import annotations

    from pathlib import Path
    import pickle
    from typing import Any
    from typing_extensions import Annotated
    import attrs
    from pytask import Product

    @attrs.define
    class PickleNode:
        path: Path
        name: str = ""
        signature: str = "id"

        def state(self) -> str | None:
            if self.path.exists():
                return str(self.path.stat().st_mtime)
            return None

        def load(self, is_product) -> Any:
            if is_product:
                return self
            return pickle.loads(self.path.read_bytes())

        def save(self, value: Any) -> None:
            self.path.write_bytes(pickle.dumps(value))

    def task_example({product_def}:
        {return_def}
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    data = pickle.loads(tmp_path.joinpath("data.pkl").read_bytes())  # noqa: S301
    assert data == 1


@pytest.mark.end_to_end()
def test_return_with_tuple_pathnode_annotation_as_return(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import PathNode

    node1 = PathNode(path=Path("file1.txt"))
    node2 = PathNode(path=Path("file2.txt"))

    def task_example() -> Annotated[str, (node1, node2)]:
        return "Hello,", "World!"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file1.txt").read_text() == "Hello,"
    assert tmp_path.joinpath("file2.txt").read_text() == "World!"


@pytest.mark.end_to_end()
def test_error_when_return_pytree_mismatch(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Any
    from typing_extensions import Annotated
    from pytask import PathNode

    node1 = PathNode(path=Path("file1.txt"))
    node2 = PathNode(path=Path("file2.txt"))

    def task_example() -> Annotated[str, (node1, node2)]:
        return "Hello,"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
    assert "Function return: PyTreeSpec(*, NoneIsLeaf)" in result.output
    assert "Return annotation: PyTreeSpec((*, *), NoneIsLeaf)" in result.output


@pytest.mark.end_to_end()
def test_pytree_and_python_node_as_return(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Any
    from typing_extensions import Annotated
    from pytask import PythonNode
    from typing import Dict

    def task_example() -> Annotated[Dict[str, str], PythonNode(name="result")]:
        return {"first": "a", "second": "b"}
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output

    # Test that python nodes are recreated every run.
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_more_nested_pytree_and_python_node_as_return_with_names(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Any
    from typing_extensions import Annotated
    from pytask import PythonNode
    from typing import Dict

    nodes = [
        PythonNode(name="dict"),
        (PythonNode(name="tuple1"), PythonNode(name="tuple2")),
        PythonNode(name="int")
    ]

    def task_example() -> Annotated[Dict[str, str], nodes]:
        return [{"first": "a", "second": "b"}, (1, 2), 1]
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_more_nested_pytree_and_python_node_as_return(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Any
    from typing_extensions import Annotated
    from pytask import PythonNode
    from typing import Dict

    nodes = [PythonNode(), (PythonNode(), PythonNode()), PythonNode()]

    def task_example() -> Annotated[Dict[str, str], nodes]:
        return [{"first": "a", "second": "b"}, (1, 2), 1]
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output


@pytest.mark.end_to_end()
def test_execute_tasks_and_pass_values_only_by_python_nodes(runner, tmp_path):
    source = """
    from pytask import PythonNode
    from typing_extensions import Annotated
    from pathlib import Path

    node_text = PythonNode(name="text")

    def task_create_text() -> Annotated[int, node_text]:
        return "This is the text."

    def task_create_file(
        text: Annotated[int, node_text]
    ) -> Annotated[str, Path("file.txt")]:
        return text
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file.txt").read_text() == "This is the text."


@pytest.mark.end_to_end()
@pytest.mark.xfail(sys.platform == "win32", reason="Decoding issues in Gitlab Actions.")
def test_execute_tasks_via_functional_api(tmp_path):
    source = """
    import sys
    from pathlib import Path
    from typing_extensions import Annotated
    from pytask import PathNode, PythonNode, build

    node_text = PythonNode()

    def create_text() -> Annotated[int, node_text]:
        return "This is the text."

    def create_file(
        content: Annotated[str, node_text]
    ) -> Annotated[str, Path("file.txt")]:
        return content

    if __name__ == "__main__":
        session = build(tasks=[create_file, create_text])
        assert len(session.tasks) == 2
        assert len(session.dag.nodes) == 5
        sys.exit(session.exit_code)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = subprocess.run(
        ("python", tmp_path.joinpath("task_module.py").as_posix()), check=False
    )
    assert result.returncode == ExitCode.OK
    assert tmp_path.joinpath("file.txt").read_text() == "This is the text."


@pytest.mark.end_to_end()
def test_pass_non_task_to_functional_api_that_are_ignored():
    session = pytask.build(tasks=None)
    assert len(session.tasks) == 0


@pytest.mark.end_to_end()
def test_multiple_product_annotations(runner, tmp_path):
    source = """
    from pytask import Product
    from typing_extensions import Annotated
    from pathlib import Path

    def task_first(
        first: Annotated[Path, Product] = Path("first.txt"),
        second: Annotated[Path, Product] = Path("second.txt")
    ):
        first.write_text("first")
        second.write_text("second")

    def task_second(
        first: Path = Path("first.txt"), second: Path = Path("second.txt")
    ):
        pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
def test_errors_during_loading_nodes_have_info(runner, tmp_path):
    source = """
    from __future__ import annotations
    from pathlib import Path
    from typing import Any
    import attrs
    import pickle

    @attrs.define
    class PickleNode:
        name: str
        path: Path
        signature: str = "id"

        def state(self) -> str | None:
            if self.path.exists():
                return str(self.path.stat().st_mtime)
            return None

        def load(self) -> Any:
            return pickle.loads(self.path.read_bytes())

        def save(self, value: Any) -> None:
            self.path.write_bytes(pickle.dumps(value))

    def task_example(
        value=PickleNode(name="node", path=Path(__file__).parent / "file.txt")
    ): pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("file.txt").touch()

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
    assert "task_example.py::task_example" in result.output
    assert "Exception while loading node" in result.output

    # Test that traceback is hidden.
    assert "_pytask/execute.py" not in result.output


@pytest.mark.end_to_end()
def test_hashing_works(tmp_path):
    """Use subprocess or otherwise the cache is filled from other tests."""
    source = """
    from pathlib import Path
    from typing_extensions import Annotated

    def task_example() -> Annotated[str, Path("file.txt")]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = subprocess.run(("pytask"), cwd=tmp_path)  # noqa: PLW1510
    assert result.returncode == ExitCode.OK

    hashes = json.loads(tmp_path.joinpath(".pytask", "file_hashes.json").read_text())
    assert len(hashes) == 2

    result = subprocess.run(("pytask"), cwd=tmp_path)  # noqa: PLW1510
    assert result.returncode == ExitCode.OK

    hashes_ = json.loads(tmp_path.joinpath(".pytask", "file_hashes.json").read_text())
    assert hashes == hashes_


@pytest.mark.end_to_end()
def test_python_node_as_product_with_product_annotation(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import Product, PythonNode
    from pathlib import Path

    node = PythonNode()

    def task_create_string(node: Annotated[PythonNode, node, Product]) -> None:
        node.save("Hello, World!")

    def task_write_file(text: Annotated[str, node]) -> Annotated[str, Path("file.txt")]:
        return text
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file.txt").read_text() == "Hello, World!"


@pytest.mark.end_to_end()
def test_pickle_node_as_product_with_product_annotation(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pytask import Product, PickleNode
    from pathlib import Path

    node = PickleNode(name="node", path=Path(__file__).parent / "file.pkl")

    def task_create_string(node: Annotated[PickleNode, node, Product]) -> None:
        node.save("Hello, World!")

    def task_write_file(text: Annotated[str, node]) -> Annotated[str, Path("file.txt")]:
        return text
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("file.txt").read_text() == "Hello, World!"


@pytest.mark.end_to_end()
def test_check_if_root_nodes_are_available(tmp_path, runner):
    source = """
    from pathlib import Path

    def task_d(path=Path("in.txt"), produces=Path("out.txt")):
        produces.write_text("1")
    """
    tmp_path.joinpath("task_d.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "NodeNotFoundError: 'task_d.py::task_d' requires" in result.output


@pytest.mark.end_to_end()
def test_check_if_root_nodes_are_available_w_name(tmp_path, runner):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated, Any
    from pytask import PathNode, PythonNode

    node1 = PathNode(name="input1", path=Path(__file__).parent / "in.txt")
    node2 = PythonNode(name="input2")

    def task_e(in1_: Annotated[Path, node1], in2_: Annotated[Any, node2]): ...
    """
    tmp_path.joinpath("task_e.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "NodeNotFoundError: 'task_e.py::task_e' requires" in result.output
    assert "input1" in result.output


@pytest.mark.end_to_end()
def test_check_if_root_nodes_are_available_with_separate_build_folder(tmp_path, runner):
    tmp_path.joinpath("src").mkdir()
    tmp_path.joinpath("bld").mkdir()
    source = """
    from pathlib import Path

    def task_d(path=Path("../bld/in.txt"), produces=Path("out.txt")):
        produces.write_text("1")
    """
    tmp_path.joinpath("src", "task_d.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.joinpath("src").as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "NodeNotFoundError: 'task_d.py::task_d' requires" in result.output
    assert "bld/in.txt" in result.output


@pytest.mark.end_to_end()
def test_error_when_node_state_throws_error(runner, tmp_path):
    source = """
    from pytask import PythonNode

    def task_example(a = PythonNode(value={"a": 1}, hash=True)):
        pass
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.FAILED
    assert "TypeError: unhashable type: 'dict'" in result.output


@pytest.mark.end_to_end()
def test_task_is_not_reexecuted(runner, tmp_path):
    source = """
    from typing_extensions import Annotated
    from pathlib import Path

    def task_first() -> Annotated[str, Path("out.txt")]:
        return "Hello, World!"

    def task_second(path = Path("out.txt")) -> Annotated[str, Path("copy.txt")]:
        return path.read_text()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "2  Succeeded" in result.output

    tmp_path.joinpath("out.txt").write_text("Changed text.")
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert "1  Skipped because unchanged" in result.output


@pytest.mark.end_to_end()
def test_use_functional_interface_with_task(tmp_path):
    def func(path):
        path.touch()

    task = TaskWithoutPath(
        name="task",
        function=func,
        produces={"path": PathNode(path=tmp_path / "out.txt")},
    )

    session = build(tasks=[task])
    assert session.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()

    session = build(tasks=task)
    assert session.exit_code == ExitCode.OK


@pytest.mark.end_to_end()
def test_collect_task(runner, tmp_path):
    source = """
    from pytask import Task, PathNode
    from pathlib import Path

    def func(path): path.touch()

    task_create_file = Task(
        base_name="task",
        function=func,
        path=Path(__file__),
        produces={"path": PathNode(path=Path(__file__).parent / "out.txt")},
    )
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end()
def test_collect_task_without_path(runner, tmp_path):
    source = """
    from pytask import TaskWithoutPath, PathNode
    from pathlib import Path

    def func(path): path.touch()

    task_create_file = TaskWithoutPath(
        name="task",
        function=func,
        produces={"path": PathNode(path=Path(__file__).parent / "out.txt")},
    )
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").exists()


@pytest.mark.end_to_end()
def test_download_file(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated
    from upath import UPath

    url = UPath(
        "https://gist.githubusercontent.com/tobiasraabe/64c24426d5398cac4b9d37b85ebfaf"
        "7c/raw/50c61fa9a5aa0b7d3a7582c4c260b43dabfea720/gistfile1.txt"
    )

    def task_download_file(path: UPath = url) -> Annotated[str, Path("data.csv")]:
        return path.read_text()
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert "Hello, World!" in tmp_path.joinpath("data.csv").read_text()
