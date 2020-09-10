import glob
from collections.abc import Iterable
from pathlib import Path

import _pytask
import pluggy


_PLUGGY_DIRECTORY = Path(pluggy.__file__).parent
_PYTASK_DIRECTORY = Path(_pytask.__file__).parent


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
        if isinstance(scalar_or_iter, str) or not isinstance(scalar_or_iter, Iterable)
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

    Since pytask uses ``None``s as a placeholder value for skippable inputs, convert the
    values.

    Examples
    --------
    >>> falsy_to_none_callback(None, None, (,))
    None
    >>> falsy_to_none_callback(None, None, [])
    None
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

    >>> get_first_non_none_value({"a": None}, {"a": "b"}, key="a", callback=to_list)
    ['b']

    """
    return next(
        (
            config[key] if callback is None else callback(config[key])
            for config in configs
            if config.get(key) is not None
        ),
        default,
    )


def remove_traceback_from_exc_info(exc_info):
    """Remove traceback from exception."""
    return (*exc_info[:2], None)


def parse_value_or_multiline_option(value):
    if isinstance(value, str) and "\n" in value:
        value = [v.strip() for v in value.split("\n") if v.strip()]
    return value


def is_internal_traceback_frame(frame):
    """Returns ``True`` if traceback frame belongs to internal packages.

    Internal packages are ``_pytask`` and ``pluggy``.

    """
    path = Path(frame.tb_frame.f_code.co_filename)
    return any(root in path.parents for root in [_PLUGGY_DIRECTORY, _PYTASK_DIRECTORY])


def filter_internal_traceback_frames(frame):
    """Filter internal traceback frames from traceback.

    If the first external frame is visited, return the frame. Else return ``None``.

    """
    for frame in yield_traceback_frames(frame):
        if frame is None or not is_internal_traceback_frame(frame):
            return frame


def remove_internal_traceback_frames_from_exc_info(exc_info):
    """Remove internal traceback frames from exception info.

    If a non-internal traceback frame is found, return the traceback from the first
    occurrence downwards. Otherwise, return the whole traceback.

    """
    if exc_info is not None:
        filtered_traceback = filter_internal_traceback_frames(exc_info[2])
        if filtered_traceback is not None:
            exc_info = (*exc_info[:2], filtered_traceback)

    return exc_info


def yield_traceback_frames(frame):
    """Yield traceback frames."""
    yield frame
    yield from yield_traceback_frames(frame.tb_next)


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
            f"Input {x} is neither truthy (True, true, 1) or falsy (False, false, 0)."
        )
    return out
