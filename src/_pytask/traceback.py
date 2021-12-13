"""Process tracebacks."""
from pathlib import Path
from types import TracebackType
from typing import Generator
from typing import Tuple
from typing import Type
from typing import Union

import _pytask
import pluggy
from rich.traceback import Traceback


_PLUGGY_DIRECTORY = Path(pluggy.__file__).parent
_PYTASK_DIRECTORY = Path(_pytask.__file__).parent


ExceptionInfo = Tuple[Type[BaseException], BaseException, Union[TracebackType, None]]


def render_exc_info(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    traceback: Union[str, TracebackType],
    show_locals: bool = False,
) -> Union[str, Traceback]:
    if isinstance(traceback, str):
        renderable = traceback
    else:
        renderable = Traceback.from_exception(
            exc_type, exc_value, traceback, show_locals=show_locals
        )

    return renderable


def format_exception_without_traceback(exc_info: ExceptionInfo) -> str:
    """Format an exception without displaying the traceback."""
    return f"[red bold]{exc_info[0].__name__}:[/] {exc_info[1]}"


def remove_traceback_from_exc_info(exc_info: ExceptionInfo) -> ExceptionInfo:
    """Remove traceback from exception."""
    return (*exc_info[:2], None)


def remove_internal_traceback_frames_from_exc_info(
    exc_info: ExceptionInfo,
) -> ExceptionInfo:
    """Remove internal traceback frames from exception info.

    If a non-internal traceback frame is found, return the traceback from the first
    occurrence downwards.

    """
    if exc_info is not None:
        if isinstance(exc_info[2], TracebackType):
            filtered_traceback = _filter_internal_traceback_frames(exc_info[2])
            exc_info = (*exc_info[:2], filtered_traceback)

    return exc_info


def _is_internal_or_hidden_traceback_frame(frame: TracebackType) -> bool:
    """Returns ``True`` if traceback frame belongs to internal packages or is hidden.

    Internal packages are ``_pytask`` and ``pluggy``. A hidden frame is indicated by a
    local variable called ``__tracebackhide__ = True``.

    """
    is_hidden = frame.tb_frame.f_locals.get("__tracebackhide__", False)
    if is_hidden:
        return True

    path = Path(frame.tb_frame.f_code.co_filename)
    return any(root in path.parents for root in [_PLUGGY_DIRECTORY, _PYTASK_DIRECTORY])


def _filter_internal_traceback_frames(
    frame: TracebackType,
) -> TracebackType:
    """Filter internal traceback frames from traceback.

    If the first external frame is visited, return the frame. Else return ``None``.

    """
    for frame in _yield_traceback_frames(frame):
        if frame is None or not _is_internal_or_hidden_traceback_frame(frame):
            break
    return frame


def _yield_traceback_frames(
    frame: TracebackType,
) -> Generator[TracebackType, None, None]:
    """Yield traceback frames."""
    yield frame
    yield from _yield_traceback_frames(frame.tb_next)
