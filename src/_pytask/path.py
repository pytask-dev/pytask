"""Contains code to handle paths."""

from __future__ import annotations

import contextlib
import functools
import importlib.util
import itertools
import os
import sys
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Sequence

from _pytask._hashlib import file_digest
from _pytask.cache import Cache

__all__ = [
    "find_case_sensitive_path",
    "find_closest_ancestor",
    "find_common_ancestor",
    "hash_path",
    "import_path",
    "relative_to",
    "shorten_path",
]


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


########################################################################################
# The following code is copied from pytest and adapted to be used in pytask.


class ImportMode(Enum):
    """Possible values for `mode` parameter of `import_path`."""

    prepend = "prepend"
    append = "append"
    importlib = "importlib"


class ImportPathMismatchError(ImportError):
    """Raised on import_path() if there is a mismatch of __file__'s.

    This can happen when `import_path` is called multiple times with different filenames
    that has the same basename but reside in packages (for example "/tests1/test_foo.py"
    and "/tests2/test_foo.py").
    """


def import_path(  # noqa: C901, PLR0912, PLR0915
    path: str | os.PathLike[str],
    *,
    mode: str | ImportMode = ImportMode.importlib,
    root: Path,
    consider_namespace_packages: bool = False,
) -> ModuleType:
    """Import and return a module from the given path.

    The module can be a file (a module) or a directory (a package).

    :param path:
        Path to the file to import.

    :param mode:
        Controls the underlying import mechanism that will be used:

        * ImportMode.prepend: the directory containing the module (or package, taking
          `__init__.py` files into account) will be put at the *start* of `sys.path`
          before being imported with `importlib.import_module`.

        * ImportMode.append: same as `prepend`, but the directory will be appended to
          the end of `sys.path`, if not already in `sys.path`.

        * ImportMode.importlib: uses more fine control mechanisms provided by
          `importlib` to import the module, which avoids having to muck with `sys.path`
          at all. It effectively allows having same-named test modules in different
          places.

    :param root:
        Used as an anchor when mode == ImportMode.importlib to obtain a unique name for
        the module being imported so it can safely be stored into ``sys.modules``.

    :param consider_namespace_packages:
        If True, consider namespace packages when resolving module names.

    :raises ImportPathMismatchError:
        If after importing the given `path` and the module `__file__` are different.
        Only raised in `prepend` and `append` modes.
    """
    path = Path(path)
    mode = ImportMode(mode)

    if not path.exists():
        raise ImportError(path)

    if mode is ImportMode.importlib:
        # Try to import this module using the standard import mechanisms, but
        # without touching sys.path.
        try:
            pkg_root, module_name = resolve_pkg_root_and_module_name(
                path, consider_namespace_packages=consider_namespace_packages
            )
        except CouldNotResolvePathError:
            pass
        else:
            # If the given module name is already in sys.modules, do not import it
            # again.
            with contextlib.suppress(KeyError):
                return sys.modules[module_name]

            mod = _import_module_using_spec(
                module_name, path, pkg_root, insert_modules=False
            )
            if mod is not None:
                return mod

        # Could not import the module with the current sys.path, so we fall back
        # to importing the file as a single module, not being a part of a package.
        module_name = _module_name_from_path(path, root)
        with contextlib.suppress(KeyError):
            return sys.modules[module_name]

        mod = _import_module_using_spec(
            module_name, path, path.parent, insert_modules=True
        )
        if mod is None:
            msg = f"Can't find module {module_name} at location {path}"
            raise ImportError(msg)
        return mod

    try:
        pkg_root, module_name = resolve_pkg_root_and_module_name(
            path, consider_namespace_packages=consider_namespace_packages
        )
    except CouldNotResolvePathError:
        pkg_root, module_name = path.parent, path.stem

    # Change sys.path permanently: restoring it at the end of this function would cause
    # surprising problems because of delayed imports: for example, a conftest.py file
    # imported by this function might have local imports, which would fail at runtime if
    # we restored sys.path.
    if mode is ImportMode.append:
        if str(pkg_root) not in sys.path:
            sys.path.append(str(pkg_root))
    elif mode is ImportMode.prepend:
        if str(pkg_root) != sys.path[0]:
            sys.path.insert(0, str(pkg_root))
    else:
        msg = f"Unknown mode: {mode}"
        raise ValueError(msg)

    importlib.import_module(module_name)

    mod = sys.modules[module_name]
    if path.name == "__init__.py":
        return mod

    ignore = os.environ.get("PY_IGNORE_IMPORTMISMATCH", "")
    if ignore != "1":
        module_file = mod.__file__
        if module_file is None:
            raise ImportPathMismatchError(module_name, module_file, path)

        if module_file.endswith((".pyc", ".pyo")):
            module_file = module_file[:-1]
        if module_file.endswith(os.sep + "__init__.py"):
            module_file = module_file[: -(len(os.sep + "__init__.py"))]

        try:
            is_same = _is_same(str(path), module_file)
        except FileNotFoundError:
            is_same = False

        if not is_same:
            raise ImportPathMismatchError(module_name, module_file, path)

    return mod


def _import_module_using_spec(
    module_name: str, module_path: Path, module_location: Path, *, insert_modules: bool
) -> ModuleType | None:
    """Import a module using the spec.

    Try to import a module by its canonical name, path to the .py file, and its parent
    location.

    :param insert_modules:
        If True, will call insert_missing_modules to create empty intermediate modules
        for made-up module names (when importing test files not reachable from
        sys.path). Note: we can probably drop insert_missing_modules altogether: instead
        of generating module names such as "src.tests.test_foo", which require
        intermediate empty modules, we might just as well generate unique module names
        like "src_tests_test_foo".
    """
    # Checking with sys.meta_path first in case one of its hooks can import this module,
    # such as our own assertion-rewrite hook.
    for meta_importer in sys.meta_path:
        spec = meta_importer.find_spec(module_name, [str(module_location)])
        if spec is not None:
            break
    else:
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    if spec is not None:
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        if insert_modules:
            _insert_missing_modules(sys.modules, module_name)
        return mod

    return None


# Implement a special _is_same function on Windows which returns True if the two
# filenames compare equal, to circumvent os.path.samefile returning False for mounts in
# UNC (#7678).
if sys.platform.startswith("win"):

    def _is_same(f1: str, f2: str) -> bool:
        return Path(f1) == Path(f2) or os.path.samefile(f1, f2)  # noqa: PTH121

else:

    def _is_same(f1: str, f2: str) -> bool:
        return os.path.samefile(f1, f2)  # noqa: PTH121


def _module_name_from_path(path: Path, root: Path) -> str:
    """
    Return a dotted module name based on the given path, anchored on root.

    For example: path="projects/src/tests/test_foo.py" and root="/projects", the
    resulting module name will be "src.tests.test_foo".
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

    When we want to import a module as "src.tests.test_foo" for example, we need
    to create empty modules "src" and "src.tests" after inserting "src.tests.test_foo",
    otherwise "src.tests.test_foo" is not importable by ``__import__``.
    """
    module_parts = module_name.split(".")
    child_module: ModuleType | None = None
    module: ModuleType | None = None
    child_name: str = ""
    while module_name:
        if module_name not in modules:
            try:
                # If sys.meta_path is empty, calling import_module will issue
                # a warning and raise ModuleNotFoundError. To avoid the
                # warning, we check sys.meta_path explicitly and raise the error
                # ourselves to fall back to creating a dummy module.
                if not sys.meta_path:
                    raise ModuleNotFoundError
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


def resolve_package_path(path: Path) -> Path | None:
    """Resolve the package path.

    Return the Python package path by looking for the last directory upwards which still
    contains an __init__.py.

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


def resolve_pkg_root_and_module_name(
    path: Path, *, consider_namespace_packages: bool = False
) -> tuple[Path, str]:
    """Resolve package root and module name.

    Return the path to the directory of the root package that contains the given Python
    file, and its module name:

    .. codeblock::
        src/
            app/
                __init__.py
                core/
                    __init__.py
                    models.py

    Passing the full path to `models.py` will yield Path("src") and "app.core.models".

    If consider_namespace_packages is True, then we additionally check upwards in the
    hierarchy until we find a directory that is reachable from sys.path, which marks it
    as a namespace package:

    https://packaging.python.org/en/latest/guides/packaging-namespace-packages

    Raises CouldNotResolvePathError if the given path does not belong to a package
    (missing any __init__.py files).
    """
    pkg_path = resolve_package_path(path)
    if pkg_path is not None:
        pkg_root = pkg_path.parent
        # https://packaging.python.org/en/latest/guides/packaging-namespace-packages/
        if consider_namespace_packages:
            # Go upwards in the hierarchy, if we find a parent path included
            # in sys.path, it means the package found by resolve_package_path()
            # actually belongs to a namespace package.
            for parent in pkg_root.parents:
                # If any of the parent paths has a __init__.py, it means it is not
                # a namespace package (see the docs linked above).
                if (parent / "__init__.py").is_file():
                    break
                if str(parent) in sys.path:
                    # Point the pkg_root to the root of the namespace package.
                    pkg_root = parent
                    break

        names = list(path.with_suffix("").relative_to(pkg_root).parts)
        if names[-1] == "__init__":
            names.pop()
        module_name = ".".join(names)
        return pkg_root, module_name

    msg = f"Could not resolve for {path}"
    raise CouldNotResolvePathError(msg)


class CouldNotResolvePathError(Exception):
    """Custom exception raised by resolve_pkg_root_and_module_name."""


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


########################################################################################


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
