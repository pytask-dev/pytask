from __future__ import annotations

import sys
import textwrap
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path
from pathlib import PurePosixPath
from pathlib import PureWindowsPath
from types import ModuleType
from typing import Any

import pytest
from _pytask.path import _insert_missing_modules
from _pytask.path import _module_name_from_path
from _pytask.path import find_case_sensitive_path
from _pytask.path import find_closest_ancestor
from _pytask.path import find_common_ancestor
from _pytask.path import relative_to
from pytask.path import import_path


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("path", "source", "include_source", "expected"),
    [
        (Path("src/hello.py"), Path("src"), True, Path("src/hello.py")),
        (Path("src/hello.py"), Path("src"), False, Path("hello.py")),
    ],
)
def test_relative_to(path, source, include_source, expected):
    result = relative_to(path, source, include_source=include_source)
    assert result == expected


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("path", "potential_ancestors", "expected"),
    [
        (Path("src/task.py"), [Path("src"), Path("bld")], Path("src")),
        (Path("tasks/task.py"), [Path("src"), Path("bld")], Path()),
        (Path("src/ts/task.py"), [Path("src"), Path("src/ts")], Path("src/ts")),
        (Path("src/in.txt"), [Path("src/task_d.py")], Path("src")),
        (Path("src/task.py"), [Path("src/task.py")], Path("src/task.py")),
    ],
)
def test_find_closest_ancestor(monkeypatch, path, potential_ancestors, expected):
    # Ensures that files are detected by an existing suffix not if they also exist.
    monkeypatch.setattr("_pytask.nodes.Path.is_file", lambda x: bool(x.suffix))
    result = find_closest_ancestor(path, potential_ancestors)
    assert result == expected


@pytest.mark.unit()
@pytest.mark.parametrize(
    ("path_1", "path_2", "expectation", "expected"),
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
            marks=pytest.mark.skipif(sys.platform != "win32", reason="fails on UNIX."),
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
            marks=pytest.mark.skipif(sys.platform != "win32", reason="fails on UNIX."),
        ),
        pytest.param(
            PureWindowsPath("C:\\home\\user\\folder_a"),
            PureWindowsPath("D:\\home\\user\\folder_b\\sub_folder"),
            pytest.raises(ValueError, match="Paths don't have the same drive"),
            None,
            id="no common ancestor",
            marks=pytest.mark.skipif(sys.platform != "win32", reason="fails on UNIX."),
        ),
    ],
)
def test_find_common_ancestor(path_1, path_2, expectation, expected):
    with expectation:
        result = find_common_ancestor(path_1, path_2)
        assert result == expected


@pytest.mark.unit()
@pytest.mark.skipif(sys.platform != "win32", reason="Only works on Windows.")
@pytest.mark.parametrize(
    ("path", "existing_paths", "expected"),
    [
        pytest.param("text.txt", [], "text.txt", id="non-existing path stays the same"),
        pytest.param("text.txt", ["text.txt"], "text.txt", id="existing path is same"),
        pytest.param("Text.txt", ["text.txt"], "text.txt", id="correct path"),
        pytest.param(
            "d/text.txt", ["D/text.txt"], "D/text.txt", id="correct path in folder"
        ),
    ],
)
def test_find_case_sensitive_path(tmp_path, path, existing_paths, expected):
    for p in (path, *existing_paths):
        p = tmp_path / p  # noqa: PLW2901
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch()

    result = find_case_sensitive_path(tmp_path / path, sys.platform)
    assert result == tmp_path / expected


@pytest.fixture()
def simple_module(request, tmp_path: Path) -> Path:
    name = f"mymod_{request.node.name}"
    fn = tmp_path / f"_src/project/{name}.py"
    fn.parent.mkdir(parents=True)
    fn.write_text("def foo(x): return 40 + x")
    module_name = _module_name_from_path(fn, root=tmp_path)
    yield fn
    sys.modules.pop(module_name, None)


@pytest.mark.unit()
def test_importmode_importlib(request, simple_module: Path, tmp_path: Path) -> None:
    """`importlib` mode does not change sys.path."""
    module = import_path(simple_module, root=tmp_path)
    assert module.foo(2) == 42  # type: ignore[attr-defined]
    assert str(simple_module.parent) not in sys.path
    assert module.__name__ in sys.modules
    assert module.__name__ == f"_src.project.mymod_{request.node.name}"
    assert "_src" in sys.modules
    assert "_src.project" in sys.modules


@pytest.mark.unit()
def test_remembers_previous_imports(simple_module: Path, tmp_path: Path) -> None:
    """importlib mode called remembers previous module (pytest#10341, pytest#10811)."""
    module1 = import_path(simple_module, root=tmp_path)
    module2 = import_path(simple_module, root=tmp_path)
    assert module1 is module2


@pytest.mark.unit()
def test_no_meta_path_found(
    simple_module: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Even without any meta_path should still import module."""
    monkeypatch.setattr(sys, "meta_path", [])
    module = import_path(simple_module, root=tmp_path)
    assert module.foo(2) == 42  # type: ignore[attr-defined]

    # mode='importlib' fails if no spec is found to load the module
    import importlib.util

    # Force module to be re-imported.
    del sys.modules[module.__name__]

    monkeypatch.setattr(
        importlib.util,
        "spec_from_file_location",
        lambda *args: None,  # noqa: ARG005
    )
    with pytest.raises(ImportError):
        import_path(simple_module, root=tmp_path)


@pytest.mark.unit()
def test_importmode_importlib_with_dataclass(tmp_path: Path) -> None:
    """
    Ensure that importlib mode works with a module containing dataclasses (#373,
    pytest#7856).
    """
    fn = tmp_path.joinpath("_src/project/task_dataclass.py")
    fn.parent.mkdir(parents=True)
    fn.write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass

            @dataclass
            class Data:
                value: str
            """
        )
    )

    module = import_path(fn, root=tmp_path)
    Data: Any = module.Data  # noqa: N806
    data = Data(value="foo")
    assert data.value == "foo"
    assert data.__module__ == "_src.project.task_dataclass"


@pytest.mark.unit()
def test_importmode_importlib_with_pickle(tmp_path: Path) -> None:
    """Ensure that importlib mode works with pickle (#373, pytest#7859)."""
    fn = tmp_path.joinpath("_src/project/task_pickle.py")
    fn.parent.mkdir(parents=True)
    fn.write_text(
        textwrap.dedent(
            """
            import pickle

            def _action():
                return 42

            def round_trip():
                s = pickle.dumps(_action)
                return pickle.loads(s)
            """
        )
    )

    module = import_path(fn, root=tmp_path)
    round_trip = module.round_trip
    action = round_trip()
    assert action() == 42


@pytest.mark.unit()
def test_importmode_importlib_with_pickle_separate_modules(tmp_path: Path) -> None:
    """
    Ensure that importlib mode works can load pickles that look similar but are
    defined in separate modules.
    """
    fn1 = tmp_path.joinpath("_src/m1/project/task.py")
    fn1.parent.mkdir(parents=True)
    fn1.write_text(
        textwrap.dedent(
            """
            import dataclasses
            import pickle

            @dataclasses.dataclass
            class Data:
                x: int = 42
            """
        )
    )

    fn2 = tmp_path.joinpath("_src/m2/project/task.py")
    fn2.parent.mkdir(parents=True)
    fn2.write_text(
        textwrap.dedent(
            """
            import dataclasses
            import pickle

            @dataclasses.dataclass
            class Data:
                x: str = ""
            """
        )
    )

    import pickle

    def round_trip(obj):
        s = pickle.dumps(obj)
        return pickle.loads(s)  # noqa: S301

    module = import_path(fn1, root=tmp_path)
    Data1 = module.Data  # noqa: N806

    module = import_path(fn2, root=tmp_path)
    Data2 = module.Data  # noqa: N806

    assert round_trip(Data1(20)) == Data1(20)
    assert round_trip(Data2("hello")) == Data2("hello")
    assert Data1.__module__ == "_src.m1.project.task"
    assert Data2.__module__ == "_src.m2.project.task"


@pytest.mark.unit()
def test_module_name_from_path(tmp_path: Path) -> None:
    result = _module_name_from_path(tmp_path / "src/project/task_foo.py", tmp_path)
    assert result == "src.project.task_foo"

    # Path is not relative to root dir: use the full path to obtain the module name.
    result = _module_name_from_path(Path("/home/foo/task_foo.py"), Path("/bar"))
    assert result == "home.foo.task_foo"

    # Importing __init__.py files should return the package as module name.
    result = _module_name_from_path(tmp_path / "src/app/__init__.py", tmp_path)
    assert result == "src.app"


@pytest.mark.unit()
def test_insert_missing_modules(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    # Use 'xxx' and 'xxy' as parent names as they are unlikely to exist and
    # don't end up being imported.
    modules = {"xxx.project.foo": ModuleType("xxx.project.foo")}
    _insert_missing_modules(modules, "xxx.project.foo")
    assert sorted(modules) == ["xxx", "xxx.project", "xxx.project.foo"]

    mod = ModuleType("mod", doc="My Module")
    modules = {"xxy": mod}
    _insert_missing_modules(modules, "xxy")
    assert modules == {"xxy": mod}

    modules = {}
    _insert_missing_modules(modules, "")
    assert not modules


@pytest.mark.unit()
def test_importlib_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """
    Importing a package using --importmode=importlib should not import the
    package's __init__.py file more than once (#11306).
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(tmp_path)

    package_name = "importlib_import_package"
    tmp_path.joinpath(package_name).mkdir()
    init = tmp_path.joinpath(f"{package_name}/__init__.py")
    init.write_text(
        textwrap.dedent(
            """
            from .singleton import Singleton
            instance = Singleton()
            """
        ),
        encoding="ascii",
    )
    singleton = tmp_path.joinpath(f"{package_name}/singleton.py")
    singleton.write_text(
        textwrap.dedent(
            """
            class Singleton:
                INSTANCES = []
                def __init__(self) -> None:
                    self.INSTANCES.append(self)
                    if len(self.INSTANCES) > 1:
                        raise RuntimeError("Already initialized")
            """
        ),
        encoding="ascii",
    )

    mod = import_path(init, root=tmp_path)
    assert len(mod.instance.INSTANCES) == 1
