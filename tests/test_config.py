import os
import textwrap

import pytest
from _pytask.config import _find_project_root_and_ini
from _pytask.config import _get_terminal_width
from _pytask.config import IGNORED_FOLDERS
from pytask import main


_IGNORED_FOLDERS = [i.split("/")[0] for i in IGNORED_FOLDERS]
_IGNORED_FOLDERS.remove("*.egg-info")


@pytest.mark.unit
@pytest.mark.parametrize(
    "in_ini, paths, expected_root, expected_ini",
    [
        ("pytask.ini", ["src/a", "src/b"], ".", "pytask.ini"),
        ("tox.ini", ["."], None, "tox.ini"),
        (None, ["task_dummy.py"], "", None),
    ],
)
def test_find_project_root_and_ini(
    tmp_path, in_ini, paths, expected_root, expected_ini
):
    if in_ini is not None:
        in_ini = tmp_path.joinpath(in_ini).resolve()
        in_ini.parent.mkdir(exist_ok=True, parents=True)
        in_ini.write_text("[pytask]")

    if expected_root is None:
        os.chdir(tmp_path)
        expected_root = tmp_path

    paths = [tmp_path.joinpath(path).resolve() for path in paths]
    for path in paths:
        if path.is_dir():
            path.mkdir(exist_ok=True, parents=True)
        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            path.touch()

    root, ini = _find_project_root_and_ini(paths)

    assert root == tmp_path.joinpath(expected_root)
    if expected_ini is None:
        assert ini is expected_ini
    else:
        assert ini == tmp_path.joinpath(expected_ini)


@pytest.mark.unit
@pytest.mark.parametrize("paths", [None, ["/mnt/home/", "C:/Users/"]])
def test_find_project_root_and_ini_raise_warning(paths):
    with pytest.warns(UserWarning, match="A common path for all passed path"):
        _find_project_root_and_ini(paths)


@pytest.mark.unit
@pytest.mark.parametrize("mock_value, expected", [(100, 99), (40, 39), (39, 79)])
def test_get_terminal_width(monkeypatch, mock_value, expected):
    def mock(**kwargs):
        return mock_value, None

    monkeypatch.setattr("_pytask.config.shutil.get_terminal_size", mock)

    assert _get_terminal_width() == expected


@pytest.mark.end_to_end
def test_debug_pytask(capsys, tmp_path):
    session = main({"paths": tmp_path, "debug_pytask": True})

    assert session.exit_code == 0

    captured = capsys.readouterr()

    # The first hooks which will be displayed.
    assert "pytask_post_parse [hook]" in captured.out
    assert "finish pytask_post_parse --> [] [hook]" in captured.out
    # The last hooks which will be displayed.
    assert "finish pytask_execute_log_end --> [True] [hook]" in captured.out
    assert "finish pytask_execute --> None [hook]" in captured.out


@pytest.mark.end_to_end
@pytest.mark.parametrize("ignored_folder", _IGNORED_FOLDERS + ["pytask.egg-info"])
def test_ignore_default_paths(tmp_path, ignored_folder):
    source = """
    def task_dummy():
        pass
    """
    tmp_path.joinpath(ignored_folder).mkdir()
    tmp_path.joinpath(ignored_folder, "task_dummy.py").write_text(
        textwrap.dedent(source)
    )

    session = main({"paths": tmp_path})
    assert session.exit_code == 0
    assert len(session.tasks) == 0


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_path", ["pytask.ini", "tox.ini", "setup.cfg"])
@pytest.mark.parametrize("ignore", ["", "*task_dummy.py"])
@pytest.mark.parametrize("new_line", [True, False])
def test_ignore_paths(tmp_path, config_path, ignore, new_line):
    source = """
    def task_dummy():
        pass
    """
    tmp_path.joinpath("task_dummy.py").write_text(textwrap.dedent(source))
    entry = f"ignore =\n\t{ignore}" if new_line else f"ignore = {ignore}"
    config = f"[pytask]\n{entry}" if ignore else "[pytask]"
    tmp_path.joinpath(config_path).write_text(config)

    session = main({"paths": tmp_path})
    assert session.exit_code == 0
    assert len(session.tasks) == 0 if ignore else len(session.tasks) == 1


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_path", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_pass_config_to_cli(tmp_path, config_path):
    config = """
    [pytask]
    markers =
      elton: Can you feel the love tonight?
    """
    tmp_path.joinpath(config_path).write_text(textwrap.dedent(config))

    os.chdir(tmp_path)
    session = main({"config": tmp_path.joinpath(config_path).as_posix()})

    assert session.exit_code == 0
    assert "elton" in session.config["markers"]


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_path", ["pytask.ini", "tox.ini", "setup.cfg"])
def test_prioritize_given_config_over_others(tmp_path, config_path):
    config = """
    [pytask]
    markers =
      kylie: I just can't get you out of my head.
    """
    tmp_path.joinpath(config_path).write_text(textwrap.dedent(config))

    for config_name in ["pytask.ini", "tox.ini", "setup.cfg"]:
        if config_name != config_path:
            config = "[pytask]\nmarkers=bad_config: Wrong config loaded"
            tmp_path.joinpath(config_name).write_text(textwrap.dedent(config))

    os.chdir(tmp_path)
    session = main({"config": tmp_path.joinpath(config_path).as_posix()})

    assert session.exit_code == 0
    assert "kylie" in session.config["markers"]


@pytest.mark.end_to_end
@pytest.mark.parametrize("config_path", ["pytask.ini", "tox.ini", "setup.cfg"])
@pytest.mark.parametrize(
    "file_or_folder",
    ["folder_a", "folder_a/task_a.py", "folder_b", "folder_b/task_b.py"],
)
def test_passing_paths_via_configuration_file(tmp_path, config_path, file_or_folder):
    config = f"""
    [pytask]
    paths =
      {file_or_folder}
    """
    tmp_path.joinpath(config_path).write_text(textwrap.dedent(config))

    for letter in ["a", "b"]:
        tmp_path.joinpath(f"folder_{letter}").mkdir()
        tmp_path.joinpath(f"folder_{letter}", f"task_{letter}.py").write_text(
            "def task_dummy(): pass"
        )

    os.chdir(tmp_path)
    session = main({})

    assert session.exit_code == 0
    assert len(session.tasks) == 1
