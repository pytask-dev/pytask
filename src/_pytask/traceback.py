"""Process tracebacks."""
from pathlib import Path

import _pytask
import pluggy

_PLUGGY_DIRECTORY = Path(pluggy.__file__).parent
_PYTASK_DIRECTORY = Path(_pytask.__file__).parent


def remove_traceback_from_exc_info(exc_info):
    """Remove traceback from exception."""
    return (*exc_info[:2], None)


def remove_internal_traceback_frames_from_exc_info(exc_info):
    """Remove internal traceback frames from exception info.

    If a non-internal traceback frame is found, return the traceback from the first
    occurrence downwards.

    """
    if exc_info is not None:
        filtered_traceback = _filter_internal_traceback_frames(exc_info[2])
        exc_info = (*exc_info[:2], filtered_traceback)

    return exc_info


def _is_internal_traceback_frame(frame):
    """Returns ``True`` if traceback frame belongs to internal packages.

    Internal packages are ``_pytask`` and ``pluggy``.

    """
    path = Path(frame.tb_frame.f_code.co_filename)
    return any(root in path.parents for root in [_PLUGGY_DIRECTORY, _PYTASK_DIRECTORY])


def _filter_internal_traceback_frames(frame):
    """Filter internal traceback frames from traceback.

    If the first external frame is visited, return the frame. Else return ``None``.

    """
    for frame in _yield_traceback_frames(frame):
        if frame is None or not _is_internal_traceback_frame(frame):
            break
    return frame


def _yield_traceback_frames(frame):
    """Yield traceback frames."""
    yield frame
    yield from _yield_traceback_frames(frame.tb_next)
