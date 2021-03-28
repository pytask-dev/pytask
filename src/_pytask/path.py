"""This module contains code to handle paths."""
from pathlib import Path
from pathlib import PurePath
from typing import List
from typing import Union


def relative_to(
    path: Union[str, Path], source: Union[str, Path], include_source: bool = True
) -> Union[str, Path]:
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
    path: Union[str, Path], potential_ancestors: List[Union[str, Path]]
) -> Path:
    """Find the closest ancestor of a path.

    In case a path is the path to the task file itself, we return the path.

    .. note::

        The check :meth:`pathlib.Path.is_file` only succeeds when the file exists. This
        must be true as otherwise an error is raised by :obj:`click` while using the
        cli.

    Examples
    --------
    >>> from pathlib import Path
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
            ancestor = ancestor.parent

        if ancestor in path.parents:
            if closest_ancestor is None or (
                len(path.relative_to(ancestor).parts)
                < len(path.relative_to(closest_ancestor).parts)
            ):
                closest_ancestor = ancestor

    return closest_ancestor


def find_common_ancestor_of_nodes(*names: str) -> Path:
    cleaned_names = [name.split("::")[0] for name in names]
    return find_common_ancestor(*cleaned_names)


def find_common_ancestor(*paths: Union[str, Path]) -> Path:
    """Find a common ancestor of many paths."""
    paths = [path if isinstance(path, PurePath) else Path(path) for path in paths]

    for path in paths:
        if not path.is_absolute():
            raise ValueError(
                f"Cannot find common ancestor for relative paths. {path} is relative."
            )

    common_parents = set.intersection(*[set(path.parents) for path in paths])

    if len(common_parents) == 0:
        raise ValueError("Paths have no common ancestor.")
    else:
        longest_parent = sorted(common_parents, key=lambda x: len(x.parts))[-1]

    return longest_parent
