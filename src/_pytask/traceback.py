"""Process tracebacks."""
from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Generator
from typing import Tuple
from typing import Type
from typing_extensions import TypeAlias
from typing import Union

import _pytask
import pluggy
from _pytask.tree_util import TREE_UTIL_LIB_DIRECTORY
from rich.traceback import Traceback


__all__ = [
    "format_exception_without_traceback",
    "remove_internal_traceback_frames_from_exception",
    "remove_internal_traceback_frames_from_exc_info",
    "remove_traceback_from_exc_info",
    "render_exc_info",
]


_PLUGGY_DIRECTORY = Path(pluggy.__file__).parent
_PYTASK_DIRECTORY = Path(_pytask.__file__).parent


ExceptionInfo: TypeAlias = Tuple[
    Type[BaseException], BaseException, Union[TracebackType, None]
]
OptionalExceptionInfo: TypeAlias = Union[ExceptionInfo, Tuple[None, None, None]]


def render_exc_info(
    exc_type: type[BaseException],
    exc_value: BaseException,
    traceback: str | TracebackType,
    *,
    show_locals: bool = False,
) -> str | Traceback:
    """Render an exception info."""
    # Can be string if send from subprocess by pytask-parallel.
    if isinstance(traceback, str):  # pragma: no cover
        return traceback
    return Traceback.from_exception(
        exc_type, exc_value, traceback, show_locals=show_locals
    )


def format_exception_without_traceback(exc_info: ExceptionInfo) -> str:
    """Format an exception without displaying the traceback."""
    return f"[red bold]{exc_info[0].__name__}:[/] {exc_info[1]}"


def remove_traceback_from_exc_info(
    exc_info: OptionalExceptionInfo,
) -> OptionalExceptionInfo:
    """Remove traceback from exception."""
    return (exc_info[0], exc_info[1], None)  # type: ignore[return-value]


def remove_internal_traceback_frames_from_exception(exc: Exception) -> Exception:
    """Remove internal traceback frames from exception.

    The conversion between exceptions and ``sys.exc_info`` is explained here:
    https://stackoverflow.com/a/59041463/7523785.

    """
    _, _, tb = remove_internal_traceback_frames_from_exc_info(
        (type(exc), exc, exc.__traceback__)
    )
    exc.__traceback__ = tb
    return exc


def remove_internal_traceback_frames_from_exc_info(
    exc_info: OptionalExceptionInfo,
) -> OptionalExceptionInfo:
    """Remove internal traceback frames from exception info.

    If a non-internal traceback frame is found, return the traceback from the first
    occurrence downwards.

    """
    if isinstance(exc_info[2], TracebackType):
        filtered_traceback = _filter_internal_traceback_frames(exc_info)
        exc_info = (*exc_info[:2], filtered_traceback)
    return exc_info


def _is_internal_or_hidden_traceback_frame(
    frame: TracebackType, exc_info: ExceptionInfo
) -> bool:
    """Returns ``True`` if traceback frame belongs to internal packages or is hidden.

    Internal packages are ``_pytask`` and ``pluggy``. A hidden frame is indicated by a
    local variable called ``__tracebackhide__ = True``.

    """
    is_hidden = frame.tb_frame.f_locals.get("__tracebackhide__", False)

    if callable(is_hidden):
        return is_hidden(exc_info)
    if is_hidden:
        return True

    path = Path(frame.tb_frame.f_code.co_filename)
    return any(
        root in path.parents
        for root in (_PLUGGY_DIRECTORY, TREE_UTIL_LIB_DIRECTORY, _PYTASK_DIRECTORY)
    )


def _filter_internal_traceback_frames(
    exc_info: ExceptionInfo,
) -> TracebackType | None:
    """Filter internal traceback frames from traceback.

    If the first external frame is visited, return the frame. Else return ``None``.

    """
    frame = exc_info[2]
    for frame_ in _yield_traceback_frames(frame):
        if frame_ is None or not _is_internal_or_hidden_traceback_frame(
            frame_, exc_info
        ):
            break
    return frame_


def _yield_traceback_frames(
    frame: TracebackType | None,
) -> Generator[TracebackType | None, None, None]:
    """Yield traceback frames."""
    yield frame
    assert frame
    yield from _yield_traceback_frames(frame.tb_next)
