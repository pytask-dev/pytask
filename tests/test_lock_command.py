from __future__ import annotations

import textwrap

import pytest

from _pytask.lockfile import read_lockfile
from pytask import ExitCode
from pytask import build
from pytask import cli


def _write_chain_project(tmp_path):
    tmp_path.joinpath("task_upstream.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_upstream(produces=Path("up.txt")):
                produces.write_text("up")
            """
        )
    )
    tmp_path.joinpath("task_downstream.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_downstream(depends_on=Path("up.txt"), produces=Path("down.txt")):
                produces.write_text(depends_on.read_text() + "down")
            """
        )
    )


def _write_marked_chain_project(tmp_path):
    tmp_path.joinpath("task_upstream.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_upstream(produces=Path("up.txt")):
                produces.write_text("up")
            """
        )
    )
    tmp_path.joinpath("task_downstream.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path

            import pytask


            @pytask.mark.try_first
            def task_downstream(depends_on=Path("up.txt"), produces=Path("down.txt")):
                produces.write_text(depends_on.read_text() + "down")
            """
        )
    )


def _task_ids(tmp_path):
    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    return {entry.id for entry in lockfile.task}


def _task_state_by_suffix(tmp_path, suffix):
    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    for entry in lockfile.task:
        if entry.id.endswith(suffix):
            return entry.state
    msg = f"Could not find lockfile entry ending with {suffix!r}."
    raise AssertionError(msg)


def _lockfile_text(tmp_path):
    return (tmp_path / "pytask.lock").read_text()


def _task_by_suffix(session, suffix):
    for task in session.tasks:
        if task.name.endswith(suffix):
            return task
    msg = f"Could not find collected task ending with {suffix!r}."
    raise AssertionError(msg)


def test_lock_help_lists_subcommands(runner):
    result = runner.invoke(cli, ["lock", "--help"])

    assert result.exit_code == ExitCode.OK
    assert "accept" in result.output
    assert "reset" in result.output
    assert "clean" in result.output


def test_build_help_no_longer_lists_clean_lockfile(runner):
    result = runner.invoke(cli, ["build", "--help"])

    assert result.exit_code == ExitCode.OK
    assert "--clean-lockfile" not in result.output


def test_lock_accept_creates_lockfile_without_executing_tasks(runner, tmp_path):
    source = """
    from pathlib import Path


    def task_example(depends_on=Path("in.txt"), produces=Path("out.txt")):
        raise RuntimeError("should not execute")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("data")
    tmp_path.joinpath("out.txt").write_text("data")

    result = runner.invoke(cli, ["lock", "accept", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert (tmp_path / "pytask.lock").exists()
    assert "should not execute" not in result.output


def test_lock_accept_can_include_ancestors(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    upstream = tmp_path / "task_upstream.py"
    downstream = tmp_path / "task_downstream.py"
    upstream_before = _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
    downstream_before = _task_state_by_suffix(
        tmp_path, "task_downstream.py::task_downstream"
    )

    upstream.write_text(upstream.read_text() + "\n# changed upstream\n")
    downstream.write_text(downstream.read_text() + "\n# changed downstream\n")

    result = runner.invoke(
        cli,
        [
            "lock",
            "accept",
            "-k",
            "downstream",
            "--with-ancestors",
            "--yes",
            tmp_path.as_posix(),
        ],
    )

    assert result.exit_code == ExitCode.OK
    assert (
        _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
        != upstream_before
    )
    assert (
        _task_state_by_suffix(tmp_path, "task_downstream.py::task_downstream")
        != downstream_before
    )


def test_lock_accept_can_include_descendants(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    upstream = tmp_path / "task_upstream.py"
    downstream = tmp_path / "task_downstream.py"
    upstream_before = _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
    downstream_before = _task_state_by_suffix(
        tmp_path, "task_downstream.py::task_downstream"
    )

    upstream.write_text(upstream.read_text() + "\n# changed upstream\n")
    downstream.write_text(downstream.read_text() + "\n# changed downstream\n")

    result = runner.invoke(
        cli,
        [
            "lock",
            "accept",
            "-k",
            "upstream",
            "--with-descendants",
            "--yes",
            tmp_path.as_posix(),
        ],
    )

    assert result.exit_code == ExitCode.OK
    assert (
        _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
        != upstream_before
    )
    assert (
        _task_state_by_suffix(tmp_path, "task_downstream.py::task_downstream")
        != downstream_before
    )


def test_lock_accept_updates_selected_task(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    before_upstream = _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
    before_downstream = _task_state_by_suffix(
        tmp_path, "task_downstream.py::task_downstream"
    )

    downstream = tmp_path / "task_downstream.py"
    downstream.write_text(downstream.read_text() + "\n# changed without rerunning\n")

    result = runner.invoke(
        cli, ["lock", "accept", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert (
        _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
        == before_upstream
    )
    assert (
        _task_state_by_suffix(tmp_path, "task_downstream.py::task_downstream")
        != before_downstream
    )


def test_lock_accept_uses_intersection_of_keyword_and_marker_selection(
    runner, tmp_path
):
    _write_marked_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    before_upstream = _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
    before_downstream = _task_state_by_suffix(
        tmp_path, "task_downstream.py::task_downstream"
    )

    downstream = tmp_path / "task_downstream.py"
    downstream.write_text(downstream.read_text() + "\n# changed downstream\n")

    result = runner.invoke(
        cli,
        [
            "lock",
            "accept",
            "-k",
            "downstream",
            "-m",
            "try_first",
            "--yes",
            tmp_path.as_posix(),
        ],
    )

    assert result.exit_code == ExitCode.OK
    assert (
        _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
        == before_upstream
    )
    assert (
        _task_state_by_suffix(tmp_path, "task_downstream.py::task_downstream")
        != before_downstream
    )


def test_lock_accept_no_matching_selection_is_a_no_op(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    before = _lockfile_text(tmp_path)

    result = runner.invoke(
        cli, ["lock", "accept", "-k", "missing", "--yes", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert "No lockfile entries need updating." in result.output
    assert _lockfile_text(tmp_path) == before


def test_lock_accept_interactive_only_applies_confirmed_changes(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    upstream = tmp_path / "task_upstream.py"
    downstream = tmp_path / "task_downstream.py"
    before_upstream = _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
    before_downstream = _task_state_by_suffix(
        tmp_path, "task_downstream.py::task_downstream"
    )

    upstream.write_text(upstream.read_text() + "\n# changed upstream\n")
    downstream.write_text(downstream.read_text() + "\n# changed downstream\n")

    result = runner.invoke(
        cli,
        [
            "lock",
            "accept",
            "-k",
            "upstream",
            "--with-descendants",
            tmp_path.as_posix(),
        ],
        input="y\nn\n",
    )

    assert result.exit_code == ExitCode.OK
    upstream_changed = (
        _task_state_by_suffix(tmp_path, "task_upstream.py::task_upstream")
        != before_upstream
    )
    downstream_changed = (
        _task_state_by_suffix(tmp_path, "task_downstream.py::task_downstream")
        != before_downstream
    )
    assert upstream_changed ^ downstream_changed


def test_lock_accept_current_task_is_a_no_op_without_rewrite(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    lockfile = tmp_path / "pytask.lock"
    before_text = lockfile.read_text()
    before_mtime = lockfile.stat().st_mtime_ns

    result = runner.invoke(
        cli, ["lock", "accept", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert "No lockfile entries need updating." in result.output
    assert lockfile.read_text() == before_text
    assert lockfile.stat().st_mtime_ns == before_mtime


def test_lock_accept_fails_for_missing_product(runner, tmp_path):
    source = """
    from pathlib import Path


    def task_example(depends_on=Path("in.txt"), produces=Path("out.txt")):
        raise RuntimeError("should not execute")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("data")

    result = runner.invoke(cli, ["lock", "accept", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "missing product" in result.output


def test_lock_accept_fails_for_missing_dependency(runner, tmp_path):
    source = """
    from pathlib import Path


    def task_example(depends_on=Path("in.txt"), produces=Path("out.txt")):
        raise RuntimeError("should not execute")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("out.txt").write_text("data")

    result = runner.invoke(cli, ["lock", "accept", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "requires missing node" in result.output


def test_lock_accept_fails_when_task_state_is_missing(runner, tmp_path):
    source = """
    from dataclasses import dataclass, field
    from pathlib import Path
    from typing import Any

    from pytask import PathNode

    @dataclass(kw_only=True)
    class CustomTask:
        name: str
        function: Any
        depends_on: dict[str, Any] = field(default_factory=dict)
        produces: dict[str, Any] = field(default_factory=dict)
        markers: list[Any] = field(default_factory=list)
        report_sections: list[tuple[str, str, str]] = field(default_factory=list)
        attributes: dict[Any, Any] = field(default_factory=dict)

        @property
        def signature(self):
            return "custom-signature"

        def state(self):
            return None

        def execute(self, **kwargs):
            return self.function(**kwargs)

    def func(path): raise RuntimeError("should not execute")

    task_create_file = CustomTask(
        name="task_custom",
        function=func,
        produces={"path": PathNode(path=Path(__file__).parent / "out.txt")},
    )
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("out.txt").write_text("done")

    result = runner.invoke(cli, ["lock", "accept", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "has no state and cannot be accepted" in result.output


def test_lock_accept_works_for_task_without_path_via_cli(runner, tmp_path):
    source = """
    from pathlib import Path

    from pytask import PathNode, TaskWithoutPath

    def func(path): raise RuntimeError("should not execute")

    task_create_file = TaskWithoutPath(
        name="task_without_path",
        function=func,
        produces={"path": PathNode(path=Path(__file__).parent / "out.txt")},
    )
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("out.txt").write_text("done")

    result = runner.invoke(cli, ["lock", "accept", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert _task_ids(tmp_path) == {"task_without_path"}


def test_lock_accept_records_custom_node_state(runner, tmp_path):
    source = """
    from dataclasses import dataclass, field
    from pathlib import Path
    from typing import Any, Annotated

    from pytask import Product

    @dataclass
    class CustomNode:
        name: str
        filepath: Path
        signature: str
        attributes: dict[Any, Any] = field(default_factory=dict)

        def state(self):
            if not self.filepath.exists():
                return None
            return self.filepath.read_text()

        def load(self, is_product=False):
            return self if is_product else self.filepath.read_text()

        def save(self, value):
            self.filepath.write_text(value)

    def task_example(
        dependency=CustomNode(
            name="custom_dependency",
            filepath=Path(__file__).parent / "in.txt",
            signature="signature-a",
        ),
        product: Annotated[CustomNode, Product] = CustomNode(
            name="custom_product",
            filepath=Path(__file__).parent / "out.txt",
            signature="signature-b",
        ),
    ):
        raise RuntimeError("should not execute")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.txt").write_text("hello")
    tmp_path.joinpath("out.txt").write_text("HELLO")

    result = runner.invoke(cli, ["lock", "accept", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    lockfile = read_lockfile(tmp_path / "pytask.lock")
    assert lockfile is not None
    entry = lockfile.task[0]
    assert "custom_dependency" in entry.depends_on
    assert "custom_product" in entry.produces


def test_lock_accept_fails_with_provisional_dependencies(runner, tmp_path):
    source = """
    from typing import Annotated
    from pathlib import Path

    from pytask import DirectoryNode

    def task_example(
        paths=DirectoryNode(pattern="*.txt")
    ) -> Annotated[str, Path("out.txt")]:
        raise RuntimeError("should not execute")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("a.txt").write_text("a")

    result = runner.invoke(cli, ["lock", "accept", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.FAILED
    assert "accepting lockfile state" in result.output


def test_lock_reset_does_not_include_ancestors_by_default(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(
        cli, ["lock", "reset", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert _task_ids(tmp_path) == {"task_upstream.py::task_upstream"}


def test_lock_reset_can_include_ancestors(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(
        cli,
        [
            "lock",
            "reset",
            "-k",
            "downstream",
            "--with-ancestors",
            "--yes",
            tmp_path.as_posix(),
        ],
    )

    assert result.exit_code == ExitCode.OK
    assert _task_ids(tmp_path) == set()


def test_lock_reset_can_include_descendants(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(
        cli,
        [
            "lock",
            "reset",
            "-k",
            "upstream",
            "--with-descendants",
            "--yes",
            tmp_path.as_posix(),
        ],
    )

    assert result.exit_code == ExitCode.OK
    assert _task_ids(tmp_path) == set()


def test_lock_reset_uses_intersection_of_keyword_and_marker_selection(runner, tmp_path):
    _write_marked_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(
        cli,
        [
            "lock",
            "reset",
            "-k",
            "downstream",
            "-m",
            "try_first",
            "--yes",
            tmp_path.as_posix(),
        ],
    )

    assert result.exit_code == ExitCode.OK
    assert _task_ids(tmp_path) == {"task_upstream.py::task_upstream"}


def test_lock_reset_no_matching_selection_is_a_no_op(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    before = _lockfile_text(tmp_path)

    result = runner.invoke(
        cli, ["lock", "reset", "-k", "missing", "--yes", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert "No lockfile entries need removing." in result.output
    assert _lockfile_text(tmp_path) == before


def test_lock_reset_when_selected_task_is_absent_is_a_no_op(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(
        cli, ["lock", "reset", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )
    assert result.exit_code == ExitCode.OK

    before = _lockfile_text(tmp_path)
    result = runner.invoke(
        cli, ["lock", "reset", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert "No lockfile entries need removing." in result.output
    assert _lockfile_text(tmp_path) == before


def test_lock_reset_interactive_only_applies_confirmed_changes(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(
        cli,
        [
            "lock",
            "reset",
            "-k",
            "upstream",
            "--with-descendants",
            tmp_path.as_posix(),
        ],
        input="y\nn\n",
    )

    assert result.exit_code == ExitCode.OK
    assert len(_task_ids(tmp_path)) == 1


def test_lock_reset_dry_run_does_not_modify_lockfile(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    before = _lockfile_text(tmp_path)

    result = runner.invoke(
        cli, ["lock", "reset", "-k", "downstream", "--dry-run", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert _lockfile_text(tmp_path) == before


def test_lock_reset_followed_by_build_reconsiders_task(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(
        cli, ["lock", "reset", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "1  Succeeded" in result.output
    assert "1  Skipped because unchanged" in result.output


def test_lock_clean_removes_stale_entries(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    tmp_path.joinpath("task_downstream.py").unlink()

    result = runner.invoke(cli, ["lock", "clean", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert _task_ids(tmp_path) == {"task_upstream.py::task_upstream"}


def test_lock_clean_dry_run_is_read_only(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    tmp_path.joinpath("task_downstream.py").unlink()
    before = _lockfile_text(tmp_path)

    result = runner.invoke(cli, ["lock", "clean", "--dry-run", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert (
        "Would remove recorded state for task_downstream.py::task_downstream."
        in result.output
    )
    assert _lockfile_text(tmp_path) == before


def test_lock_clean_interactive_only_applies_confirmed_changes(runner, tmp_path):
    tmp_path.joinpath("task_alpha.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_alpha(produces=Path("alpha.txt")):
                produces.write_text("alpha")
            """
        )
    )
    tmp_path.joinpath("task_beta.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_beta(produces=Path("beta.txt")):
                produces.write_text("beta")
            """
        )
    )

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    tmp_path.joinpath("task_alpha.py").unlink()
    tmp_path.joinpath("task_beta.py").unlink()

    result = runner.invoke(
        cli,
        ["lock", "clean", tmp_path.as_posix()],
        input="y\nn\n",
    )

    assert result.exit_code == ExitCode.OK
    assert len(_task_ids(tmp_path)) == 1


def test_lock_clean_reports_when_no_stale_entries_exist(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(cli, ["lock", "clean", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "There are no stale lockfile entries." in result.output


def test_lock_clean_on_fresh_project_without_lockfile_is_harmless(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, ["lock", "clean", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "There are no stale lockfile entries." in result.output
    assert not (tmp_path / "pytask.lock").exists()


def test_lock_clean_removes_multiple_stale_entries_without_adding_new_ones(
    runner, tmp_path
):
    tmp_path.joinpath("task_alpha.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_alpha(produces=Path("alpha.txt")):
                produces.write_text("alpha")
            """
        )
    )
    tmp_path.joinpath("task_beta.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_beta(produces=Path("beta.txt")):
                produces.write_text("beta")
            """
        )
    )

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    tmp_path.joinpath("task_alpha.py").unlink()
    tmp_path.joinpath("task_beta.py").unlink()
    tmp_path.joinpath("task_gamma.py").write_text(
        textwrap.dedent(
            """
            from pathlib import Path


            def task_gamma(produces=Path("gamma.txt")):
                produces.write_text("gamma")
            """
        )
    )

    result = runner.invoke(cli, ["lock", "clean", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert _task_ids(tmp_path) == set()


def test_lock_accept_followed_by_build_skips_changed_task(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    downstream = tmp_path / "task_downstream.py"
    downstream.write_text(downstream.read_text() + "\n# changed downstream\n")

    result = runner.invoke(
        cli, ["lock", "accept", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )
    assert result.exit_code == ExitCode.OK

    result = runner.invoke(cli, [tmp_path.as_posix()])

    assert result.exit_code == ExitCode.OK
    assert "2  Skipped because unchanged" in result.output


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{not toml", "Lockfile has invalid format"),
        ('lock-version = "0.9"\ntask = []\n', "Unsupported lock-version"),
        ('lock-version = "9.0"\ntask = []\n', "Unsupported lock-version"),
    ],
)
def test_lock_commands_fail_for_invalid_lockfiles(runner, tmp_path, content, message):
    _write_chain_project(tmp_path)
    tmp_path.joinpath("pytask.lock").write_text(content)

    result = runner.invoke(cli, ["lock", "clean", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.CONFIGURATION_FAILED
    assert message in result.output


def test_lock_accept_on_database_only_project_creates_lockfile(runner, tmp_path):
    _write_chain_project(tmp_path)

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert (tmp_path / ".pytask" / "pytask.sqlite3").exists()

    (tmp_path / "pytask.lock").unlink()

    downstream = tmp_path / "task_downstream.py"
    downstream.write_text(downstream.read_text() + "\n# changed downstream\n")

    result = runner.invoke(
        cli, ["lock", "accept", "-k", "downstream", "--yes", tmp_path.as_posix()]
    )

    assert result.exit_code == ExitCode.OK
    assert (tmp_path / "pytask.lock").exists()


@pytest.mark.parametrize("subcommand", ["accept", "reset", "clean"])
def test_lock_rejects_dry_run_and_yes_together(runner, tmp_path, subcommand):
    _write_chain_project(tmp_path)

    args = ["lock", subcommand, "--dry-run", "--yes", tmp_path.as_posix()]
    result = runner.invoke(cli, args)

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


@pytest.mark.parametrize("subcommand", ["accept", "reset", "clean"])
def test_lock_commands_replay_journal_before_applying_changes(
    runner, tmp_path, subcommand
):
    _write_chain_project(tmp_path)

    session = build(paths=tmp_path)
    assert session.exit_code == ExitCode.OK

    lockfile_state = session.config["lockfile_state"]
    assert lockfile_state is not None

    downstream = tmp_path / "task_downstream.py"
    downstream.write_text(downstream.read_text() + "\n# journal change\n")
    downstream_task = _task_by_suffix(session, "task_downstream.py::task_downstream")
    lockfile_state.update_task(session, downstream_task)

    journal_path = (tmp_path / "pytask.lock").with_suffix(".lock.journal")
    assert journal_path.exists()

    if subcommand == "accept":
        downstream.write_text(downstream.read_text() + "\n# current change\n")
        args = ["lock", "accept", "-k", "downstream", "--yes", tmp_path.as_posix()]
    elif subcommand == "reset":
        args = ["lock", "reset", "-k", "downstream", "--yes", tmp_path.as_posix()]
    else:
        tmp_path.joinpath("task_downstream.py").unlink()
        args = ["lock", "clean", "--yes", tmp_path.as_posix()]

    result = runner.invoke(cli, args)

    assert result.exit_code == ExitCode.OK
    assert not journal_path.exists()


def test_lock_command_fails_for_ambiguous_lockfile_ids(runner, tmp_path):
    source = """
    from dataclasses import dataclass, field
    from pathlib import Path
    from typing import Any

    @dataclass
    class CustomNode:
        name: str
        value: str
        signature: str
        attributes: dict[Any, Any] = field(default_factory=dict)

        def state(self):
            return self.value

        def load(self, is_product=False):
            return self.value

        def save(self, value):
            self.value = value

    def task_example(
        first=CustomNode(name="dup", value="1", signature="signature-a"),
        second=CustomNode(name="dup", value="2", signature="signature-b"),
        produces=Path("out.txt"),
    ):
        raise RuntimeError("should not execute")
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, ["lock", "clean", "--yes", tmp_path.as_posix()])

    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "Ambiguous lockfile ids detected" in result.output
