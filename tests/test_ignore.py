from pathlib import Path

import pytest
from _pytask.collect import pytask_ignore_collect
from _pytask.config import IGNORED_FOLDERS
from pytask import main


@pytest.mark.end_to_end
@pytest.mark.parametrize("ignored_folder", IGNORED_FOLDERS + ["pytask.egg-info"])
def test_ignore_default_paths(tmp_path, ignored_folder):
    folder = ignored_folder.split("/*")[0]
    tmp_path.joinpath(folder).mkdir()
    tmp_path.joinpath(folder, "task_dummy.py").write_text("def task_d(): pass")

    session = main({"paths": tmp_path})
    assert session.exit_code == 0
    assert len(session.tasks) == 0


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_path", ["pytask.ini", "tox.ini", "setup.cfg"])
@pytest.mark.parametrize("ignore", ["", "*task_dummy.py"])
@pytest.mark.parametrize("new_line", [True, False])
def test_ignore_paths(tmp_path, config_path, ignore, new_line):
    tmp_path.joinpath("task_dummy.py").write_text("def task_dummy(): pass")
    entry = f"ignore =\n\t{ignore}" if new_line else f"ignore = {ignore}"
    config = f"[pytask]\n{entry}" if ignore else "[pytask]"
    tmp_path.joinpath(config_path).write_text(config)

    session = main({"paths": tmp_path})
    assert session.exit_code == 0
    assert len(session.tasks) == 0 if ignore else len(session.tasks) == 1


@pytest.mark.unit
@pytest.mark.parametrize(
    "path, ignored_paths, expected",
    [
        (Path("example").resolve(), ["example"], True),
        (Path("example", "file.py").resolve(), ["example"], False),
        (Path("example", "file.py").resolve(), ["example/*"], True),
    ],
)
def test_pytask_ignore_collect(path, ignored_paths, expected):
    is_ignored = pytask_ignore_collect(path, {"ignore": ignored_paths})
    assert is_ignored == expected
