"""Functions which are used across various modules."""
import glob
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import List


def to_list(scalar_or_iter):
    """Convert scalars and iterables to list.

    Parameters
    ----------
    scalar_or_iter : str or list

    Returns
    -------
    list

    Examples
    --------
    >>> to_list("a")
    ['a']
    >>> to_list(["b"])
    ['b']

    """
    return (
        [scalar_or_iter]
        if isinstance(scalar_or_iter, str) or not isinstance(scalar_or_iter, Sequence)
        else list(scalar_or_iter)
    )


def parse_paths(x):
    """Parse paths."""
    if x is not None:
        paths = [Path(p) for p in to_list(x)]
        paths = [
            Path(p).resolve() for path in paths for p in glob.glob(path.as_posix())
        ]
        return paths


def falsy_to_none_callback(ctx, param, value):  # noqa: U100
    """Convert falsy object to ``None``.

    Some click arguments accept multiple inputs and instead of ``None`` as a default if
    no information is passed, they return empty lists or tuples.

    Since pytask uses ``None`` as a placeholder value for skippable inputs, convert the
    values.

    Examples
    --------
    >>> falsy_to_none_callback(None, None, ()) is None
    True
    >>> falsy_to_none_callback(None, None, []) is None
    True
    >>> falsy_to_none_callback(None, None, 1)
    1

    """
    return value if value else None


def get_first_non_none_value(*configs, key, default=None, callback=None):
    """Get the first non-None value for a key from a list of dictionaries.

    This function allows to prioritize information from many configurations by changing
    the order of the inputs while also providing a default.

    Examples
    --------
    >>> get_first_non_none_value({"a": None}, {"a": 1}, key="a")
    1
    >>> get_first_non_none_value({"a": None}, {"a": None}, key="a", default="default")
    'default'
    >>> get_first_non_none_value({}, {}, key="a", default="default")
    'default'
    >>> get_first_non_none_value({"a": None}, {"a": "b"}, key="a")
    'b'

    """
    callback = (lambda x: x) if callback is None else callback  # noqa: E731
    processed_values = (callback(config.get(key)) for config in configs)
    return next((value for value in processed_values if value is not None), default)


def parse_value_or_multiline_option(value):
    """Parse option which can hold a single value or values separated by new lines."""
    if value in ["none", "None", None, ""]:
        value = None
    elif isinstance(value, str) and "\n" in value:
        value = [v.strip() for v in value.split("\n") if v.strip()]
    elif isinstance(value, str) and "n" not in value:
        value = value.strip()
    return value


def convert_truthy_or_falsy_to_bool(x):
    """Convert truthy or falsy value in .ini to Python boolean."""
    if x in [True, "True", "true", "1"]:
        out = True
    elif x in [False, "False", "false", "0"]:
        out = False
    elif x in [None, "None", "none"]:
        out = None
    else:
        raise ValueError(
            f"Input '{x}' is neither truthy (True, true, 1) or falsy (False, false, 0)."
        )
    return out


def find_duplicates(x: Iterable[Any]):
    """Find duplicated entries in iterable.

    Examples
    --------
    >>> find_duplicates(["a", "b", "a"])
    {'a'}
    >>> find_duplicates(["a", "b"])
    set()

    """
    seen = set()
    duplicates = set()

    for i in x:
        if i in seen:
            duplicates.add(i)
        seen.add(i)

    return duplicates


def create_task_name(path: Path, base_name: str):
    """Create the name of a task from a path and the task's base name.

    Examples
    --------
    >>> from pathlib import Path
    >>> create_task_name(Path("module.py"), "task_dummy")
    'module.py::task_dummy'

    """
    return path.as_posix() + "::" + base_name


def relative_to(path: Path, source: Path, include_source: bool = True):
    """Make a path relative to another path.

    In contrast to :meth:`pathlib.Path.relative_to`, this function allows to keep the
    name of the source path.

    Examples
    --------
    >>> from pathlib import Path
    >>> relative_to(Path("folder", "file.py"), Path("folder")).as_posix()
    'folder/file.py'
    >>> relative_to(Path("folder", "file.py"), Path("folder"), False).as_posix()
    'file.py'

    """
    return Path(source.name if include_source else "", path.relative_to(source))


def find_closest_ancestor(path: Path, potential_ancestors: List[Path]):
    """Find the closest ancestor of a path.

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
        if ancestor in path.parents:
            if closest_ancestor is None or (
                len(path.relative_to(ancestor).parts)
                < len(path.relative_to(closest_ancestor).parts)
            ):
                closest_ancestor = ancestor

    return closest_ancestor


def shorten_task_name(task, paths: List[Path]):
    """Shorten the task name.

    By default, the whole task name is used in while reporting execution errors. This
    leads to incomprehensible long names when using nested folder structures in bigger
    projects. Thus, print a shorter name which uses only the path from the passed
    'paths' down to the task file.

    Examples
    --------
    >>> from pathlib import Path
    >>> class Task: pass
    >>> task = Task()
    >>> task.path = Path("/home/user/task_example.py")
    >>> task.base_name = "task_example_function"

    >>> shorten_task_name(task, [Path("/home/user")])
    'user/task_example.py::task_example_function'

    >>> shorten_task_name(task, [Path("/home/user/task_example.py")])
    'task_example.py::task_example_function'

    >>> shorten_task_name(task, [Path("/etc")])
    Traceback (most recent call last):
    ValueError: A task must be defined in one of 'paths'.

    """
    ancestor = find_closest_ancestor(task.path, paths)
    if ancestor is None:
        raise ValueError("A task must be defined in one of 'paths'.")
    elif ancestor == task.path:
        name = create_task_name(Path(task.path.name), task.base_name)
    else:
        shortened_path = relative_to(task.path, ancestor)
        name = create_task_name(shortened_path, task.base_name)

    return name
