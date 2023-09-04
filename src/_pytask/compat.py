"""Contains functions to assess compatibility and optional dependencies."""
from __future__ import annotations

import importlib
import shutil
import sys
import warnings
from typing import TYPE_CHECKING

from packaging.version import parse as parse_version

if TYPE_CHECKING:
    import types


__all__ = ["check_for_optional_program", "import_optional_dependency"]


_MINIMUM_VERSIONS: dict[str, str] = {}
"""Dict[str, str]: A mapping from packages to their minimum versions."""


_IMPORT_TO_PACKAGE_NAME: dict[str, str] = {}
"""Dict[str, str]: A mapping from import name to package name (on PyPI) for packages
where these two names are different."""


def _get_version(module: types.ModuleType) -> str:
    """Get version from a package."""
    version = getattr(module, "__version__", None)
    if version is None:
        msg = f"Can't determine version for {module.__name__}"
        raise ImportError(msg)
    return version


def import_optional_dependency(
    name: str,
    extra: str = "",
    errors: str = "raise",
    min_version: str | None = None,
    caller: str = "pytask",
) -> types.ModuleType | None:
    """Import an optional dependency.

    By default, if a dependency is missing an ImportError with a nice message will be
    raised. If a dependency is present, but too old, we raise.

    Parameters
    ----------
    name
        The module name.
    extra
        Additional text to include in the ImportError message.
    errors
        What to do when a dependency is not found or its version is too old.

        * raise : Raise an ImportError
        * warn : Only applicable when a module's version is to old. Warns that the
          version is too old and returns None
        * ignore: If the module is not installed, return None, otherwise, return the
          module, even if the version is too old. It's expected that users validate the
          version locally when using ``errors="ignore"`` (see. ``io/html.py``)
    min_version
        Specify a minimum version that is different from the global pandas minimum
        version required.
    caller
        The caller of the function.

    Returns
    -------
    types.ModuleType | None
        The imported module, when found and the version is correct. None is returned
        when the package is not found and `errors` is False, or when the package's
        version is too old and `errors` is ``'warn'``.

    """
    if errors not in ("warn", "raise", "ignore"):  # pragma: no cover
        msg = "'errors' must be one of 'warn', 'raise' or 'ignore'."
        raise ValueError(msg)

    package_name = _IMPORT_TO_PACKAGE_NAME.get(name)
    install_name = package_name if package_name is not None else name

    if extra and not extra.endswith(" "):
        extra += " "
    msg = (
        f"{caller} requires the optional dependency {install_name!r}. {extra}"
        f"Use pip or conda to install {install_name!r}."
    )
    try:
        module = importlib.import_module(name)
    except ImportError:
        if errors == "raise":
            raise ImportError(msg) from None
        return None

    # Handle submodules: if we have submodule, grab parent module from sys.modules
    parent = name.split(".")[0]
    if parent != name:
        install_name = parent
        module_to_get = sys.modules[install_name]
    else:
        module_to_get = module
    minimum_version = (
        min_version if min_version is not None else _MINIMUM_VERSIONS.get(parent)
    )
    if minimum_version:
        version = _get_version(module_to_get)
        if parse_version(version) < parse_version(minimum_version):
            msg = (
                f"{caller} requires version {minimum_version!r} or newer of "
                f"{parent!r} (version {version!r} currently installed)."
            )
            if errors == "warn":
                warnings.warn(msg, UserWarning, stacklevel=2)
                return None
            if errors == "raise":
                raise ImportError(msg)

    return module


def check_for_optional_program(
    name: str,
    extra: str = "",
    errors: str = "raise",
    caller: str = "pytask",
) -> bool | None:
    """Check whether an optional program exists."""
    if errors not in ("warn", "raise", "ignore"):
        msg = f"'errors' must be one of 'warn', 'raise' or 'ignore' and not {errors!r}."
        raise ValueError(msg)

    msg = f"{caller} requires the optional program {name!r}. {extra}"

    program_exists = shutil.which(name) is not None

    if not program_exists:
        if errors == "raise":
            raise RuntimeError(msg)
        if errors == "warn":
            warnings.warn(msg, UserWarning, stacklevel=2)

    return program_exists
