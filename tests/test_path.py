from pathlib import Path

import pytest
from _pytask.path import find_closest_ancestor
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
