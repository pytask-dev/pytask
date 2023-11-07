"""Process tracebacks."""
from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import ClassVar
from typing import Generator
from typing import Tuple
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

import _pytask
import pluggy
from _pytask.outcomes import Exit
from _pytask.tree_util import TREE_UTIL_LIB_DIRECTORY
from attrs import define
from rich.traceback import Traceback as RichTraceback

if TYPE_CHECKING:
    from rich.console import ConsoleOptions
    from rich.console import Console
    from rich.console import RenderResult
    from typing_extensions import TypeAlias


__all__ = [
    "Traceback",
    "remove_internal_traceback_frames_from_exc_info",
    "remove_traceback_from_exc_info",
]


_PLUGGY_DIRECTORY = Path(pluggy.__file__).parent
_PYTASK_DIRECTORY = Path(_pytask.__file__).parent


ExceptionInfo: TypeAlias = Tuple[
    Type[BaseException], BaseException, Union[TracebackType, None]
]
OptionalExceptionInfo: TypeAlias = Union[ExceptionInfo, Tuple[None, None, None]]


@define
class Traceback:
    exc_info: OptionalExceptionInfo

    show_locals: ClassVar[bool] = False
    suppress: ClassVar[tuple[Path, ...]] = (
        _PLUGGY_DIRECTORY,
        TREE_UTIL_LIB_DIRECTORY,
        _PYTASK_DIRECTORY,
    )

    def __rich_console__(
        self, console: Console, console_options: ConsoleOptions
    ) -> RenderResult:
        if self.exc_info and isinstance(self.exc_info[1], Exit):
            self.exc_info = remove_traceback_from_exc_info(self.exc_info)

        filtered_exc_info = remove_internal_traceback_frames_from_exc_info(
            self.exc_info, suppress=self.suppress
        )

        # The tracebacks returned by pytask-parallel are strings.
        if isinstance(filtered_exc_info[2], str):
            yield filtered_exc_info[2]
        else:
            yield RichTraceback.from_exception(
                *filtered_exc_info, show_locals=self.show_locals
            )


def remove_traceback_from_exc_info(
    exc_info: OptionalExceptionInfo,
) -> OptionalExceptionInfo:
    """Remove traceback from exception."""
    return (exc_info[0], exc_info[1], None)  # type: ignore[return-value]


def remove_internal_traceback_frames_from_exc_info(
    exc_info: OptionalExceptionInfo,
    suppress: tuple[Path, ...] = (
        _PLUGGY_DIRECTORY,
        TREE_UTIL_LIB_DIRECTORY,
        _PYTASK_DIRECTORY,
    ),
) -> OptionalExceptionInfo:
    """Remove internal traceback frames from exception info.

    If a non-internal traceback frame is found, return the traceback from the first
    occurrence downwards.

    """
    if isinstance(exc_info[1], Exception):
        exc_info[1].__cause__ = _remove_internal_traceback_frames_from_exception(
            exc_info[1].__cause__
        )

    if isinstance(exc_info[2], TracebackType):
        filtered_traceback = _filter_internal_traceback_frames(exc_info, suppress)
        exc_info = (*exc_info[:2], filtered_traceback)
    return exc_info


def _remove_internal_traceback_frames_from_exception(
    exc: BaseException | None,
) -> BaseException | None:
    """Remove internal traceback frames from exception.

    The conversion between exceptions and ``sys.exc_info`` is explained here:
    https://stackoverflow.com/a/59041463/7523785.

    """
    if exc is None:
        return exc

    _, _, tb = remove_internal_traceback_frames_from_exc_info(
        (type(exc), exc, exc.__traceback__)
    )
    exc.__traceback__ = tb
    return exc


def _is_internal_or_hidden_traceback_frame(
    frame: TracebackType,
    exc_info: ExceptionInfo,
    suppress: tuple[Path, ...] = (
        _PLUGGY_DIRECTORY,
        TREE_UTIL_LIB_DIRECTORY,
        _PYTASK_DIRECTORY,
    ),
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
    return any(root in path.parents for root in suppress)


def _filter_internal_traceback_frames(
    exc_info: ExceptionInfo, suppress: tuple[Path, ...]
) -> TracebackType | None:
    """Filter internal traceback frames from traceback.

    If the first external frame is visited, return the frame. Else return ``None``.

    """
    frame = exc_info[2]
    for frame_ in _yield_traceback_frames(frame):
        if frame_ is None or not _is_internal_or_hidden_traceback_frame(
            frame_, exc_info, suppress
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
