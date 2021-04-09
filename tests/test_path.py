from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path
from pathlib import PurePosixPath
from pathlib import PureWindowsPath

import pytest
from _pytask.path import find_closest_ancestor
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to


@pytest.mark.unit
@pytest.mark.parametrize(
    "path, source, include_source, expected",
    [
        (Path("src/hello.py"), Path("src"), True, Path("src/hello.py")),
        (Path("src/hello.py"), Path("src"), False, Path("hello.py")),
    ],
)
def test_relative_to(path, source, include_source, expected):
    result = relative_to(path, source, include_source)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "path, potential_ancestors, expected",
    [
        (Path("src/task.py"), [Path("src"), Path("bld")], Path("src")),
        (Path("tasks/task.py"), [Path("src"), Path("bld")], None),
        (Path("src/ts/task.py"), [Path("src"), Path("src/ts")], Path("src/ts")),
        (Path("src/in.txt"), [Path("src/task_d.py")], Path("src")),
        (Path("src/task.py"), [Path("src/task.py")], Path("src/task.py")),
    ],
)
def test_find_closest_ancestor(monkeypatch, path, potential_ancestors, expected):
    # Ensures that files are detected by an existing suffix not if they also exist.
    monkeypatch.setattr("_pytask.nodes.pathlib.Path.is_file", lambda x: bool(x.suffix))
    result = find_closest_ancestor(path, potential_ancestors)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "path_1, path_2, expectation, expected",
    [
        pytest.param(
            PurePosixPath("relative_1"),
            PurePosixPath("/home/relative_2"),
            pytest.raises(ValueError, match="Can't mix absolute and relative paths"),
            None,
            id="test path 1 is relative",
        ),
        pytest.param(
            PureWindowsPath("C:/home/relative_1"),
            PureWindowsPath("relative_2"),
            pytest.raises(ValueError, match="Can't mix absolute and relative paths"),
            None,
            id="test path 2 is relative",
        ),
        pytest.param(
            PurePosixPath("/home/user/folder_a"),
            PurePosixPath("/home/user/folder_b/sub_folder"),
            does_not_raise(),
            Path("/home/user"),
            id="normal behavior with UNIX paths",
        ),
        pytest.param(
            PureWindowsPath("C:\\home\\user\\folder_a"),
            PureWindowsPath("C:\\home\\user\\folder_b\\sub_folder"),
            does_not_raise(),
            PureWindowsPath("C:\\home\\user"),
            id="normal behavior with Windows paths",
        ),
        pytest.param(
            PureWindowsPath("C:\\home\\user\\folder_a"),
            PureWindowsPath("D:\\home\\user\\folder_b\\sub_folder"),
            pytest.raises(ValueError, match="Paths don't have the same drive"),
            None,
            id="no common ancestor",
        ),
    ],
)
def test_find_common_ancestor(path_1, path_2, expectation, expected):
    with expectation:
        result = find_common_ancestor(path_1, path_2)
        assert result == expected
