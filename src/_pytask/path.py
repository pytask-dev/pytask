"""Contains code to handle paths."""

from __future__ import annotations

import contextlib
import functools
import importlib.machinery
import importlib.util
import itertools
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from _pytask._hashlib import file_digest
from _pytask.cache import Cache

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "find_case_sensitive_path",
    "find_closest_ancestor",
    "find_common_ancestor",
    "hash_path",
    "import_path",
    "relative_to",
    "shorten_path",
]


def relative_to(path: Path, source: Path, *, include_source: bool = True) -> Path:
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


def find_closest_ancestor(
    path: Path, potential_ancestors: Sequence[Path]
) -> Path | None:
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
    potential_closest_ancestors = []
    for ancestor in potential_ancestors:
        if ancestor == path:
            return path

        with contextlib.suppress(ValueError):
            candidate = find_common_ancestor(path, ancestor)
            potential_closest_ancestors.append(candidate)

    return next(
        (
            i
            for i in sorted(
                potential_closest_ancestors, key=lambda x: len(x.parts), reverse=True
            )
        ),
        None,
    )


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

    The functions are taken from pytest when the import mode is set to ``importlib``. It
    was assumed to be the new default import mode but insurmountable tradeoffs caused
    the default to be set to ``prepend``. More discussion and information can be found
    in :issue:`373`.

    """
    try:
        pkg_root, module_name = _resolve_pkg_root_and_module_name(path)
    except CouldNotResolvePathError:
        pass
    else:
        # If the given module name is already in sys.modules, do not import it again.
        with contextlib.suppress(KeyError):
            return sys.modules[module_name]

        mod = _import_module_using_spec(module_name, path, pkg_root)
        if mod is not None:
            return mod

    module_name = _module_name_from_path(path, root)
    with contextlib.suppress(KeyError):
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, str(path))

    if spec is None:
        msg = f"Can't find module {module_name!r} at location {path}."
        raise ImportError(msg)

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    _insert_missing_modules(sys.modules, module_name)
    return mod


def _resolve_package_path(path: Path) -> Path | None:
    """Resolve package path.

    Return the Python package path by looking for the last directory upwards which still
    contains an ``__init__.py``.

    Returns None if it can not be determined.

    """
    result = None
    for parent in itertools.chain((path,), path.parents):
        if parent.is_dir():
            if not (parent / "__init__.py").is_file():
                break
            if not parent.name.isidentifier():
                break
            result = parent
    return result


def _resolve_pkg_root_and_module_name(path: Path) -> tuple[Path, str]:
    """Resolve the root package directory and module name for the given Python file.

    Return the path to the directory of the root package that contains the given Python
    file, and its module name:

    .. code-block:: text

        src/
            app/
                __init__.py core/
                    __init__.py models.py

    Passing the full path to `models.py` will yield Path("src") and "app.core.models".

    This function also handles namespace packages (directories without __init__.py)
    by walking up the directory tree and checking if Python's import system can
    resolve the computed module name to the given path. This prevents double-imports
    when task files import each other using Python's standard import mechanism.

    Raises CouldNotResolvePathError if the given path does not belong to a package
    (missing any __init__.py files) and no valid namespace package root is found.

    """
    # First, try to find a regular package (with __init__.py files).
    pkg_path = _resolve_package_path(path)
    if pkg_path is not None:
        pkg_root = pkg_path.parent
        module_name = _compute_module_name(pkg_root, path)
        if module_name:
            return pkg_root, module_name

    # No regular package found. Check for namespace packages by walking up the
    # directory tree and verifying that Python's import system would resolve
    # the computed module name to this file.
    for candidate in (path.parent, *path.parent.parents):
        module_name = _compute_module_name(candidate, path)
        if module_name and _is_importable(module_name, path):
            # Found a root where Python's import system agrees with our module name.
            return candidate, module_name

    msg = f"Could not resolve for {path}"
    raise CouldNotResolvePathError(msg)


class CouldNotResolvePathError(Exception):
    """Custom exception raised by _resolve_pkg_root_and_module_name."""


def _spec_matches_module_path(
    module_spec: importlib.machinery.ModuleSpec | None, module_path: Path
) -> bool:
    """Return true if the given ModuleSpec can be used to import the given module path.

    Handles both regular modules (via origin) and namespace packages
    (via submodule_search_locations).

    """
    if module_spec is None:
        return False

    if module_spec.origin:
        return Path(module_spec.origin) == module_path

    # For namespace packages, check submodule_search_locations.
    # https://docs.python.org/3/library/importlib.html#importlib.machinery.ModuleSpec.submodule_search_locations
    if module_spec.submodule_search_locations:
        for location in module_spec.submodule_search_locations:
            if Path(location) == module_path:
                return True

    return False


def _is_importable(module_name: str, module_path: Path) -> bool:
    """Check if a module name would resolve to the given path using Python's import.

    This verifies that importing `module_name` via Python's standard import mechanism
    (as if typed in the REPL) would load the file at `module_path`.

    Note: find_spec() has a side effect of creating parent namespace packages in
    sys.modules. We clean these up to avoid polluting the module namespace.
    """
    # Track modules before the call to clean up side effects
    modules_before = set(sys.modules.keys())

    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, ValueError, ImportWarning):
        return False
    finally:
        # Clean up any modules that were added as side effects.
        # find_spec() can create parent namespace packages in sys.modules.
        modules_added = set(sys.modules.keys()) - modules_before
        for mod_name in modules_added:
            sys.modules.pop(mod_name, None)

    return _spec_matches_module_path(spec, module_path)


def _compute_module_name(root: Path, module_path: Path) -> str | None:
    """Compute a module name based on a path and a root anchor.

    Returns None if the module name cannot be computed.

    """
    try:
        path_without_suffix = module_path.with_suffix("")
    except ValueError:
        return None

    try:
        relative = path_without_suffix.relative_to(root)
    except ValueError:
        return None

    names = list(relative.parts)
    if not names:
        return None
    if names[-1] == "__init__":
        names.pop()
    return ".".join(names) if names else None


def _import_module_using_spec(
    module_name: str, module_path: Path, module_location: Path
) -> ModuleType | None:
    """Import a module using its specification.

    Tries to import a module by its canonical name, path to the .py file, and its parent
    location.

    """
    # Checking with sys.meta_path first in case one of its hooks can import this module,
    # such as our own assertion-rewrite hook.
    for meta_importer in sys.meta_path:
        try:
            spec = meta_importer.find_spec(module_name, [str(module_location)])
        except (ImportError, KeyError, ValueError):
            # Some meta_path finders raise exceptions when parent modules don't exist.
            continue
        if spec is not None:
            break
    else:
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is not None:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)  # ty: ignore[possibly-missing-attribute]
        _insert_missing_modules(sys.modules, module_name)
        return mod

    return None


def _module_name_from_path(path: Path, root: Path) -> str:
    """Return a dotted module name based on the given path, anchored on root.

    For example: path="projects/src/tasks/task_foo.py" and root="/projects", the
    resulting module name will be "src.tasks.task_foo".

    """
    path = path.with_suffix("")
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        # If we can't get a relative path to root, use the full path, except
        # for the first part ("d:\\" or "/" depending on the platform, for example).
        path_parts = path.parts[1:]
    else:
        # Use the parts for the relative path to the root path.
        path_parts = relative_path.parts

    # Module name for packages do not contain the __init__ file, unless
    # the `__init__.py` file is at the root.
    if len(path_parts) >= 2 and path_parts[-1] == "__init__":  # noqa: PLR2004
        path_parts = path_parts[:-1]

    # Module names cannot contain ".", normalize them to "_". This prevents a directory
    # having a "." in the name (".env.310" for example) causing extra intermediate
    # modules. Also, important to replace "." at the start of paths, as those are
    # considered relative imports.
    path_parts = tuple(x.replace(".", "_") for x in path_parts)

    return ".".join(path_parts)


def _insert_missing_modules(modules: dict[str, ModuleType], module_name: str) -> None:
    """Insert missing modules in sys.modules.

    Used by ``import_path`` to create intermediate modules when using mode=importlib.
    When we want to import a module as "src.tasks.task_foo" for example, we need to
    create empty modules "src" and "src.tasks" after inserting "src.tasks.task_foo",
    otherwise "src.tasks.task_foo" is not importable by ``__import__``.

    """
    module_parts = module_name.split(".")
    child_module: ModuleType | None = None
    module: ModuleType | None = None
    child_name: str = ""
    while module_name:
        if module_name not in modules:
            try:
                # If sys.meta_path is empty, calling import_module will issue a warning
                # and raise ModuleNotFoundError. To avoid the warning, we check
                # sys.meta_path explicitly and raise the error ourselves to fall back to
                # creating a dummy module.
                if not sys.meta_path:
                    raise ModuleNotFoundError  # noqa: TRY301
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                module = ModuleType(
                    module_name,
                    doc="Empty module created by pytest's importmode=importlib.",
                )
        else:
            module = modules[module_name]
        # Add child attribute to the parent that can reference the child modules.
        if child_module and not hasattr(module, child_name):
            setattr(module, child_name, child_module)
            modules[module_name] = module
        # Keep track of the child module while moving up the tree.
        child_module, child_name = module, module_name.rpartition(".")[-1]
        module_parts.pop(-1)
        module_name = ".".join(module_parts)


def shorten_path(path: Path, paths: Sequence[Path]) -> str:
    """Shorten a path.

    The whole path of a node - which includes the drive letter - can be very long
    when using nested folder structures in bigger projects.

    Thus, the part of the name which contains the path is replaced by the relative
    path from one path in ``session.config["paths"]`` to the node.

    """
    ancestor = find_closest_ancestor(path, paths)
    if ancestor is None:
        try:
            ancestor = find_common_ancestor(path, *paths)
        except ValueError:
            ancestor = path.parents[-1]

    return relative_to(path, ancestor).as_posix()


HashPathCache = Cache()


@HashPathCache.memoize
def hash_path(
    path: Path,
    modification_time: float,  # noqa: ARG001
    digest: str = "sha256",
) -> str:
    """Compute the hash of a file.

    The function is connected to a cache that is warmed up with previous hashes during
    the configuration phase.

    """
    with path.open("rb") as f:
        hash_ = file_digest(f, digest)
    return hash_.hexdigest()
