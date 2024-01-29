from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner
from nbmake.pytest_items import NotebookItem
from packaging import version
from pytask import console
from pytask import storage


@pytest.fixture(autouse=True)
def _add_objects_to_doctest_namespace(doctest_namespace):
    doctest_namespace["Path"] = Path


@pytest.fixture(autouse=True, scope="session")
def _path_for_snapshots():
    console.width = 80


def _remove_variable_info_from_output(data: str, path: Any) -> str:  # noqa: ARG001
    lines = data.splitlines()

    # Remove dynamic versions.
    index_root = next(i for i, line in enumerate(lines) if line.startswith("Root:"))
    new_info_line = "".join(lines[1:index_root])
    for platform in ("linux", "win32", "darwin"):
        new_info_line = new_info_line.replace(platform, "<platform>")
    pattern = re.compile(version.VERSION_PATTERN, flags=re.IGNORECASE | re.VERBOSE)
    new_info_line = re.sub(pattern=pattern, repl="<version>", string=new_info_line)

    # Remove dynamic root path
    index_collected = next(
        i for i, line in enumerate(lines) if line.startswith("Collected")
    )
    new_root_line = "Root: <path>"

    new_lines = [lines[0], new_info_line, new_root_line, *lines[index_collected:]]
    return "\n".join(new_lines)


@pytest.fixture()
def snapshot_cli(snapshot):
    return snapshot.with_defaults(matcher=_remove_variable_info_from_output)


class SysPathsSnapshot:
    """A snapshot for sys.path."""

    def __init__(self) -> None:
        self.__saved = list(sys.path), list(sys.meta_path)

    def restore(self) -> None:
        sys.path[:], sys.meta_path[:] = self.__saved


class SysModulesSnapshot:
    """A snapshot for sys.modules."""

    def __init__(self) -> None:
        self.__saved = dict(sys.modules)

    def restore(self) -> None:
        sys.modules.clear()
        sys.modules.update(self.__saved)


@contextmanager
def restore_sys_path_and_module_after_test_execution():
    sys_path_snapshot = SysPathsSnapshot()
    sys_modules_snapshot = SysModulesSnapshot()
    yield
    sys_modules_snapshot.restore()
    sys_path_snapshot.restore()


@pytest.fixture(autouse=True)
def _restore_sys_path_and_module_after_test_execution():
    """Restore sys.path and sys.modules after every test execution.

    This fixture became necessary because most task modules in the tests are named
    `task_example`. Since the change in #424, the same module is not reimported which
    solves errors with parallelization. At the same time, modules with the same name in
    the tests are overshadowing another and letting tests fail.

    The changes to `sys.path` might not be necessary to restore, but we do it anyways.

    """
    with restore_sys_path_and_module_after_test_execution():
        yield


class CustomCliRunner(CliRunner):
    def invoke(self, *args, **kwargs):
        """Restore sys.path and sys.modules after an invocation."""
        storage.create()
        with restore_sys_path_and_module_after_test_execution():
            return super().invoke(*args, **kwargs)


@pytest.fixture()
def runner():
    return CustomCliRunner()


def pytest_collection_modifyitems(session, config, items) -> None:  # noqa: ARG001
    """Add markers to Jupyter notebook tests."""
    for item in items:
        if isinstance(item, NotebookItem):
            item.add_marker(pytest.mark.xfail(reason="The tests are flaky."))
