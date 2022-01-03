"""This module contains code to handle paths."""
import functools
import os
from pathlib import Path
from typing import Sequence
from typing import Union


def relative_to(
    path: Union[str, Path], source: Union[str, Path], include_source: bool = True
) -> Path:
    """Make a path relative to another path.

    In contrast to :meth:`pathlib.Path.relative_to`, this function allows to keep the
    name of the source path.

    Examples
    --------
    The default behavior of :mod:`pathlib` is to exclude the source path from the
    relative path.

    >>> relative_to("folder/file.py", "folder", False).as_posix()
    'file.py'

    To provide relative locations to users, it is sometimes more helpful to provide the
    source as an orientation.

    >>> relative_to("folder/file.py", "folder").as_posix()
    'folder/file.py'

    """
    source_name = Path(source).name if include_source else ""
    return Path(source_name, Path(path).relative_to(source))


def find_closest_ancestor(
    path: Union[str, Path], potential_ancestors: Sequence[Union[str, Path]]
) -> Path:
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
    if isinstance(path, str):
        path = Path(path)

    closest_ancestor = None
    for ancestor in potential_ancestors:

        if isinstance(ancestor, str):
            ancestor = Path(ancestor)

        if ancestor == path:
            closest_ancestor = path
            break

        # Paths can also point to files in which case we want to take the parent folder.
        if ancestor.is_file():
            ancestor = ancestor.parent

        if ancestor in path.parents:
            if closest_ancestor is None or (
                len(path.relative_to(ancestor).parts)
                < len(path.relative_to(closest_ancestor).parts)
            ):
                closest_ancestor = ancestor

    return closest_ancestor


def find_common_ancestor_of_nodes(*names: str) -> Path:
    """Find the common ancestor from task names and nodes."""
    cleaned_names = [name.split("::")[0] for name in names]
    return find_common_ancestor(*cleaned_names)


def find_common_ancestor(*paths: Union[str, Path]) -> Path:
    """Find a common ancestor of many paths."""
    common_ancestor = Path(os.path.commonpath(paths))
    return common_ancestor


@functools.lru_cache()
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
    if platform == "win32":
        out = path.resolve()
    else:
        out = path
    return out
