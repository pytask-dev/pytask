from __future__ import annotations

import textwrap

import cloudpickle
import pytest

from _pytask.pluginmanager import get_plugin_manager
from pytask import CollectionOutcome
from pytask import ExitCode
from pytask import TaskOutcome
from pytask import build
from pytask import cli
from pytask import hookimpl


def test_task_that_produces_provisional_path_node(tmp_path):
    source = """
    from typing import Annotated
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


def test_task_that_depends_on_relative_provisional_path_node(tmp_path):
    source = """
    from typing import Annotated
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


def test_task_that_depends_on_provisional_path_node_with_absolute_root_dir(tmp_path):
    source = """
    from typing import Annotated
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


def test_task_that_depends_on_provisional_path_node_with_relative_root_dir(tmp_path):
    source = """
    from typing import Annotated
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


def test_task_that_depends_on_provisional_task(runner, tmp_path):
    source = """
    from typing import Annotated
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


def test_gracefully_fail_when_dag_raises_error(runner, tmp_path):
    source = """
    from typing import Annotated
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


@pytest.mark.parametrize("future_annotations", [False, True])
def test_provisional_task_generation(runner, tmp_path, future_annotations):
    future_import = "from __future__ import annotations" if future_annotations else ""
    source = f"""
    {future_import}
    from typing import Annotated
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
    assert tmp_path.joinpath("a-copy.txt").read_text() == "Hello, "
    assert tmp_path.joinpath("b-copy.txt").read_text() == "World!"


@pytest.mark.parametrize("future_annotations", [False, True])
@pytest.mark.parametrize("decorator", ["@task", "@task()"])
def test_generated_annotations_snapshot_locals_without_parameter_defaults(
    tmp_path, future_annotations, decorator
):
    future_import = "from __future__ import annotations" if future_annotations else ""
    source = f"""
    {future_import}
    from pathlib import Path
    from typing import Annotated
    from pytask import task

    @task(is_generator=True)
    def task_generator():
        for i in range(2):
            output = Path(f"out-{{i}}.txt")

            {decorator}
            def task_example() -> Annotated[str, output]:
                return "generated"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 3
    assert tmp_path.joinpath("out-0.txt").read_text() == "generated"
    assert tmp_path.joinpath("out-1.txt").read_text() == "generated"


@pytest.mark.parametrize("fail_collection", [False, True])
def test_generated_annotation_snapshots_are_released_after_collection(
    tmp_path, fail_collection
):
    annotation = "unknown" if fail_collection else "output"
    source = f"""
    from __future__ import annotations
    import threading
    import weakref
    from pathlib import Path
    from typing import Annotated
    from pytask import task

    class Payload:
        pass

    references = []

    @task(is_generator=True)
    def task_generator():
        lock = threading.RLock()
        payload = Payload()
        references.append(weakref.ref(payload))

        for i in range(2):
            output = Path(f"out-{{i}}.txt")

            @task
            def task_example() -> Annotated[str, {annotation}]:
                return "generated"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == (ExitCode.FAILED if fail_collection else ExitCode.OK)
    children = [
        report.node
        for report in session.collection_reports
        if report.node is not None and "task_example" in report.node.name
    ]
    assert len(children) == 2
    for child in children:
        assert child.function.pytask_meta.annotation_locals is None
        cloudpickle.dumps(child.function)

    if not fail_collection:
        generator = next(
            task for task in session.tasks if task.name.endswith("task_generator")
        )
        references = generator.function.__globals__["references"]
        assert len(references) == 1
        assert references[0]() is None


@pytest.mark.parametrize("future_annotations", [False, True])
@pytest.mark.parametrize(
    "exception", ["RuntimeError('generator failed')", "SystemExit(7)"]
)
def test_failed_generator_releases_child_annotation_snapshots(
    tmp_path, future_annotations, exception
):
    future_import = "from __future__ import annotations" if future_annotations else ""
    source = f"""
    {future_import}
    import threading
    from pytask import task

    children = []
    error = {exception}

    @task(is_generator=True)
    def task_generator():
        lock = threading.RLock()
        for i in range(2):
            @task
            def task_child():
                raise AssertionError("Child must not execute")
            children.append(task_child)
        raise error
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.FAILED
    assert len(session.tasks) == 1
    assert len(session.execution_reports) == 1
    report = session.execution_reports[0]
    assert report.outcome == TaskOutcome.FAIL
    assert report.exc_info is not None
    namespace = report.task.function.__globals__
    assert report.exc_info[1] is namespace["error"]
    assert len(namespace["children"]) == 2
    for child in namespace["children"]:
        assert child.pytask_meta.annotation_locals is None
        cloudpickle.dumps(child)


def test_task_generator_executes_once(tmp_path):
    source = """
    from pathlib import Path
    from pytask import task

    @task(is_generator=True)
    def task_generator():
        counter = Path(__file__).parent / "counter.txt"
        count = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(count + 1))

        @task
        def task_generated(produces=Path(__file__).parent / "generated.txt"):
            produces.write_text("generated")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.OK
    assert tmp_path.joinpath("counter.txt").read_text() == "1"
    assert tmp_path.joinpath("generated.txt").read_text() == "generated"
    assert len(session.tasks) == 2
    assert len(session.execution_reports) == 2


def test_task_generator_return_annotation_is_rejected(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Annotated
    from pytask import task

    @task(is_generator=True)
    def task_generator() -> Annotated[
        str, Path("returned.txt")
    ]:
        @task
        def task_child(produces=Path("child.txt")):
            produces.write_text("child")

        return "ignored"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "cannot define products" in result.output
    assert "return annotation" in result.output


def test_task_generator_decorator_return_product_is_ignored(tmp_path):
    source = """
    from pathlib import Path
    from pytask import task

    @task(is_generator=True, produces=Path("returned.txt"))
    def task_generator():
        @task
        def task_child(produces=Path("child.txt")):
            produces.write_text("child")

        return "ignored"
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)
    generator = next(
        task for task in session.tasks if task.name.endswith("task_generator")
    )

    assert session.exit_code == ExitCode.OK
    assert tmp_path.joinpath("child.txt").read_text() == "child"
    assert not tmp_path.joinpath("returned.txt").exists()
    assert "return" not in generator.produces


@pytest.mark.parametrize("mode", ["dry_run", "explain"])
def test_task_generator_in_simulation_mode(tmp_path, mode):
    source = """
    from pathlib import Path
    from pytask import task

    @task(is_generator=True)
    def task_generator():
        counter = Path(__file__).parent / "counter.txt"
        count = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(count + 1))

        @task
        def task_generated(produces=Path(__file__).parent / "generated.txt"):
            produces.write_text("generated")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(
        paths=tmp_path, dry_run=mode == "dry_run", explain=mode == "explain"
    )

    outcomes = {
        report.task.name.rsplit("::", maxsplit=1)[-1]: report.outcome
        for report in session.execution_reports
    }
    assert session.exit_code == ExitCode.OK
    assert outcomes == {
        "task_generator": TaskOutcome.WOULD_BE_EXECUTED,
        "task_generated": TaskOutcome.WOULD_BE_EXECUTED,
    }
    assert tmp_path.joinpath("counter.txt").read_text() == "1"
    assert not tmp_path.joinpath("generated.txt").exists()


def test_failed_generated_task_collection_is_atomic(tmp_path):
    source = """
    from pathlib import Path
    from typing import Annotated
    from pytask import task

    @task(is_generator=True)
    def task_generator():
        counter = Path(__file__).parent / "counter.txt"
        count = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(count + 1))

        @task
        def task_valid(produces=Path(__file__).parent / "valid.txt"):
            produces.write_text("valid")

        @task
        def task_invalid() -> Annotated[int, 1]:
            return 1

    def task_unrelated(produces=Path(__file__).parent / "unrelated.txt"):
        produces.write_text("unrelated")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.FAILED
    assert tmp_path.joinpath("counter.txt").read_text() == "1"
    assert not tmp_path.joinpath("valid.txt").exists()
    assert tmp_path.joinpath("unrelated.txt").read_text() == "unrelated"
    assert len(session.tasks) == 2
    assert [report.outcome for report in session.execution_reports].count(
        TaskOutcome.FAIL
    ) == 1
    generated_reports = [
        report
        for report in session.collection_reports
        if report.node is not None
        and report.node.name.endswith(("task_valid", "task_invalid"))
    ]
    assert len(generated_reports) == 2
    assert {report.outcome for report in generated_reports} == {
        CollectionOutcome.SUCCESS,
        CollectionOutcome.FAIL,
    }


def test_task_generator_cannot_define_products_with_argument(runner, tmp_path):
    source = """
    from pathlib import Path
    from pytask import task

    @task(is_generator=True)
    def task_generator(produces=Path("generator.txt")):
        @task
        def task_child():
            pass
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "cannot define products" in result.output


def test_gracefully_fail_when_task_generator_raises_error(runner, tmp_path):
    source = """
    from typing import Annotated
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


def test_use_provisional_node_as_product_in_generator_without_rerun(runner, tmp_path):
    source = """
    from typing import Annotated
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


def test_root_dir_is_created(runner, tmp_path):
    source = """
    from typing import Annotated
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


@pytest.mark.parametrize("collision_in_wrapper", [False, True])
def test_generated_task_identity_conflict_stops_before_dag_rebuild(
    tmp_path, monkeypatch, collision_in_wrapper
):
    source = """
    from pathlib import Path
    from pytask import task, mark

    def task_existing():
        Path(__file__).with_name("existing-ran").touch()

    @mark.try_first
    @task(is_generator=True)
    def task_generator():
        @task(name=GENERATED_NAME)
        def generated():
            Path(__file__).with_name("generated-ran").touch()
    """
    generated_name = "task_generated" if collision_in_wrapper else "task_existing"
    source = source.replace("GENERATED_NAME", repr(generated_name))
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    class Plugin:
        @hookimpl(wrapper=True)
        def pytask_collect_modify_tasks(self, tasks):
            result = yield
            for task in tasks:
                if task.base_name == "task_generated":
                    task.base_name = "task_existing"
            return result

    pm = get_plugin_manager()
    pm.register(Plugin())
    monkeypatch.setattr("_pytask.build.get_plugin_manager", lambda: pm)
    session = build(paths=tmp_path, force=True)

    assert session.exit_code == ExitCode.FAILED
    assert session.should_stop
    assert not tmp_path.joinpath("existing-ran").exists()
    assert not tmp_path.joinpath("generated-ran").exists()
    assert any(
        report.exc_info and "Conflicting task identities" in str(report.exc_info[1])
        for report in session.execution_reports
    )
    assert len(session.tasks) == 2
    assert len(session.dag.nodes) == 2


def test_generator_failed_dag_rebuild_restores_execution_state(tmp_path, monkeypatch):
    source = """
    from pathlib import Path
    from pytask import task

    def task_existing(produces=Path(__file__).with_name("same.txt")):
        produces.write_text("existing")

    @task(is_generator=True)
    def task_generator():
        @task
        def task_child(produces=Path(__file__).with_name("same.txt")):
            produces.write_text("child")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    previous = {}

    class Plugin:
        @hookimpl
        def pytask_execute_task(self, session):
            previous.update(
                tasks=session.tasks, dag=session.dag, scheduler=session.scheduler
            )

    pm = get_plugin_manager()
    pm.register(Plugin())
    monkeypatch.setattr("_pytask.build.get_plugin_manager", lambda: pm)

    session = build(paths=tmp_path)

    assert session.exit_code == ExitCode.FAILED
    assert session.should_stop
    assert session.tasks is previous["tasks"]
    assert session.dag is previous["dag"]
    assert session.scheduler is previous["scheduler"]
    assert len(session.tasks) == 2
    assert any(
        r.exc_info and "same output" in str(r.exc_info[1])
        for r in session.execution_reports
    )
