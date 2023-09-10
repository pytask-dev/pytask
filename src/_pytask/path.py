"""Contains code to handle paths."""
from __future__ import annotations

import functools
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence


def relative_to(path: Path, source: Path, include_source: bool = True) -> Path:
    """Make a path relative to another path.

    In contrast to :meth:`pathlib.Path.relative_to`, this function allows to keep the
    name of the source path.

    Examples
    --------
    The default behavior of :mod:`pathlib` is to exclude the source path from the
    relative path.

    >>> relative_to(Path("folder/file.py"), Path("folder"), False).as_posix()
    'file.py'

    To provide relative locations to users, it is sometimes more helpful to provide the
    source as an orientation.

    >>> relative_to(Path("folder/file.py"), Path("folder")).as_posix()
    'folder/file.py'

    """
    source_name = source.name if include_source else ""
    return Path(source_name, path.relative_to(source))


def find_closest_ancestor(path: Path, potential_ancestors: Sequence[Path]) -> Path:
    """Find the closest ancestor of a path.

    In case a path is the path to the task file itself, we return the path.

    .. note::

        The check :meth:`pathlib.Path.is_file` only succeeds when the file exists. This
        must be true as otherwise an error is raised by :obj:`click` while using the
        cli.

    Examples
    --------
    >>> find_closest_ancestor(Path("folder", "file.py"), [Path("folder")]).as_posix()
    'folder'

    >>> paths = [Path("folder"), Path("folder", "subfolder")]
    >>> find_closest_ancestor(Path("folder", "subfolder", "file.py"), paths).as_posix()
    'folder/subfolder'

    """
    closest_ancestor = None
    for ancestor in potential_ancestors:
        if ancestor == path:
            closest_ancestor = path
            break

        # Paths can also point to files in which case we want to take the parent folder.
        if ancestor.is_file():
            ancestor = ancestor.parent  # noqa: PLW2901

        if ancestor in path.parents and (
            closest_ancestor is None
            or (
                len(path.relative_to(ancestor).parts)
                < len(path.relative_to(closest_ancestor).parts)
            )
        ):
            closest_ancestor = ancestor

    return closest_ancestor


def find_common_ancestor_of_nodes(*names: str) -> Path:
    """Find the common ancestor from task names and nodes."""
    cleaned_names = [Path(name.split("::")[0]) for name in names]
    return find_common_ancestor(*cleaned_names)


def find_common_ancestor(*paths: Path) -> Path:
    """Find a common ancestor of many paths."""
    return Path(os.path.commonpath(paths))


@functools.lru_cache
def find_case_sensitive_path(path: Path, platform: str) -> Path:
    """Find the case-sensitive path.

    On case-insensitive file systems (mostly Windows and Mac), a path like ``text.txt``
    and ``TeXt.TxT`` would point to the same file but not on case-sensitive file
    systems.

    On Windows, we can use :meth:`pathlib.Path.resolve` to find the real path.

    This does not work on POSIX systems since Python implements them as if they are
    always case-sensitive. Some observations:

    - On case-sensitive POSIX systems, :meth:`pathlib.Path.exists` fails with a
      case-insensitive path.
    - On case-insensitive POSIX systems, :meth:`pathlib.Path.exists` succeeds with a
      case-insensitive path.
    - On case-insensitive POSIX systems, :meth:`pathlib.Path.resolve` does not return
      a case-sensitive path which it does on Windows.

    """
    return path.resolve() if platform == "win32" else path


def import_path(path: Path, root: Path) -> ModuleType:
    """Import and return a module from the given path.

    The function is taken from pytest when the import mode is set to ``importlib``. It
    pytest's recommended import mode for new projects although the default is set to
    ``prepend``. More discussion and information can be found in :gh:`373`.

    """
    module_name = _module_name_from_path(path, root)

    spec = importlib.util.spec_from_file_location(module_name, str(path))

    if spec is None:
        msg = f"Can't find module {module_name!r} at location {path}."
        raise ImportError(msg)

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    _insert_missing_modules(sys.modules, module_name)
    return mod


def _module_name_from_path(path: Path, root: Path) -> str:
    """Return a dotted module name based on the given path, anchored on root.

    For example: path="projects/src/project/task_foo.py" and root="/projects", the
    resulting module name will be "src.project.task_foo".

    """
    path = path.with_suffix("")
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        # If we can't get a relative path to root, use the full path, except for the
        # first part ("d:\\" or "/" depending on the platform, for example).
        path_parts = path.parts[1:]
    else:
        # Use the parts for the relative path to the root path.
        path_parts = relative_path.parts

    return ".".join(path_parts)


def _insert_missing_modules(modules: dict[str, ModuleType], module_name: str) -> None:
    """Insert missing modules when importing modules with :func:`import_path`.

    When we want to import a module as ``src.project.task_foo`` for example, we need to
    create empty modules ``src`` and ``src.project`` after inserting
    ``src.project.task_foo``, otherwise ``src.project.task_foo`` is not importable by
    ``__import__``.

    """
    module_parts = module_name.split(".")
    while module_name:
        if module_name not in modules:
            try:
                # If sys.meta_path is empty, calling import_module will issue a warning
                # and raise ModuleNotFoundError. To avoid the warning, we check
                # sys.meta_path explicitly and raise the error ourselves to fall back to
                # creating a dummy module.
                if not sys.meta_path:
                    raise ModuleNotFoundError
                importlib.import_module(module_name)
            except ModuleNotFoundError:
                module = ModuleType(
                    module_name,
                    doc="Empty module created by pytask.",
                )
                modules[module_name] = module
        module_parts.pop(-1)
        module_name = ".".join(module_parts)
