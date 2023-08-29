from __future__ import annotations

from pathlib import Path

import pytest
from _pytask.collect import pytask_ignore_collect
from _pytask.config import _IGNORED_FOLDERS
from pytask import build
from pytask import ExitCode


@pytest.mark.end_to_end()
@pytest.mark.parametrize("ignored_folder", [*_IGNORED_FOLDERS, "pytask.egg-info"])
def test_ignore_default_paths(tmp_path, ignored_folder):
    folder = ignored_folder.split("/*")[0]
    tmp_path.joinpath(folder).mkdir()
    tmp_path.joinpath(folder, "task_module.py").write_text("def task_d(): pass")

    session = build(paths=tmp_path)
    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 0


@pytest.mark.end_to_end()
@pytest.mark.parametrize("ignore", ["", "*task_module.py"])
@pytest.mark.parametrize("new_line", [True, False])
def test_ignore_paths(tmp_path, ignore, new_line):
    tmp_path.joinpath("task_module.py").write_text("def task_example(): pass")
    entry = f"ignore = ['{ignore}']" if new_line else f"ignore = '{ignore}'"
    config = (
        f"[tool.pytask.ini_options]\n{entry}" if ignore else "[tool.pytask.ini_options]"
    )
    tmp_path.joinpath("pyproject.toml").write_text(config)

    session = build(paths=tmp_path)
    assert session.exit_code == ExitCode.OK
    assert len(session.tasks) == 0 if ignore else len(session.tasks) == 1


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("path", "ignored_paths", "expected"),
    [
        (Path("example").resolve(), ["example"], True),
        (Path("example", "file.py").resolve(), ["example"], False),
        (Path("example", "file.py").resolve(), ["example/*"], True),
    ],
)
def test_pytask_ignore_collect(path, ignored_paths, expected):
    is_ignored = pytask_ignore_collect(path, {"ignore": ignored_paths})
    assert is_ignored == expected
