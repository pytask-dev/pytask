from __future__ import annotations

import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from typing import Callable

import pytest
from click.testing import CliRunner
from packaging import version
from pytask import console


@pytest.fixture(autouse=True)
def _add_objects_to_doctest_namespace(doctest_namespace):
    doctest_namespace["Path"] = Path


@pytest.fixture(autouse=True, scope="session")
def _path_for_snapshots():
    console.width = 80


def _remove_variable_info_from_output(data: str, path: Any) -> str:  # noqa: ARG001
    new_lines = []
    for line in data.splitlines():
        if line.startswith("Platform"):
            for platform in ("linux", "win32", "debian"):
                line = line.replace(platform, "<platform>")  # noqa: PLW2901
            pattern = re.compile(
                version.VERSION_PATTERN, flags=re.IGNORECASE | re.VERBOSE
            )
            line = re.sub(  # noqa: PLW2901
                pattern=pattern, repl="<version>", string=line
            )
        elif line.startswith("Root:"):
            line = "Root: <path>"  # noqa: PLW2901
        new_lines.append(line)
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

    def __init__(self, preserve: Callable[[str], bool] | None = None) -> None:
        self.__preserve = preserve
        self.__saved = dict(sys.modules)

    def restore(self) -> None:
        if self.__preserve:
            self.__saved.update(
                (k, m) for k, m in sys.modules.items() if self.__preserve(k)
            )
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
        with restore_sys_path_and_module_after_test_execution():
            return super().invoke(*args, **kwargs)


@pytest.fixture()
def runner():
    return CustomCliRunner()
