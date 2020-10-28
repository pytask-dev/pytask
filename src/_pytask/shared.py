"""Functions which are used across various modules."""
import glob
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from typing import Iterable


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
