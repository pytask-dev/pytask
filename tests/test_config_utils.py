from __future__ import annotations

import pytest
from _pytask.config_utils import _find_project_root_and_config


@pytest.mark.unit
@pytest.mark.parametrize(
    "config_filename, paths, expected_root, expected_config",
    [
        ("pyproject.toml", ["src/a", "src/b"], ".", "pyproject.toml"),
        ("pyproject.toml", ["."], None, "pyproject.toml"),
        (None, ["task_module.py"], "", None),
    ],
)
def test_find_project_root_and_config(
    tmp_path, config_filename, paths, expected_root, expected_config
):
    if config_filename is not None:
        config_filename = tmp_path.joinpath(config_filename).resolve()
        config_filename.parent.mkdir(exist_ok=True, parents=True)
        config_filename.write_text("[tool.pytask.ini_options]")

    if expected_root is None:
        expected_root = tmp_path

    paths = [tmp_path.joinpath(path).resolve() for path in paths]
    for path in paths:
        if path.is_dir():
            path.mkdir(exist_ok=True, parents=True)
        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            path.touch()

    root, config = _find_project_root_and_config(paths)

    assert root == tmp_path.joinpath(expected_root)
    if expected_config is None:
        assert config is expected_config
    else:
        assert config == tmp_path.joinpath(expected_config)


@pytest.mark.unit
@pytest.mark.parametrize("paths", [None, ["/mnt/home/", "C:/Users/"]])
def test_find_project_root_and_config_raise_warning(paths):
    with pytest.warns(UserWarning, match="A common path for all passed path"):
        _find_project_root_and_config(paths)


@pytest.mark.unit
@pytest.mark.parametrize(
    "vc_folder, path, expected",
    [
        (".git", "folder/sub", "."),
        (None, "folder/sub", "folder/sub"),
    ],
)
def test_root_stops_at_version_control_folder(tmp_path, vc_folder, path, expected):
    if vc_folder:
        tmp_path.joinpath(vc_folder).mkdir(parents=True)

    root, ini = _find_project_root_and_config([tmp_path.joinpath(path)])

    assert ini is None
    assert root == tmp_path.joinpath(expected)
