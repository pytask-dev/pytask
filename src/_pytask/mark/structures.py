from __future__ import annotations

import warnings
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from attrs import define
from attrs import field
from attrs import validators

from _pytask.mark_utils import get_all_marks
from _pytask.models import CollectionMetadata
from _pytask.typing import is_task_function

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Mapping


@define(frozen=True)
class Mark:
    """A class for a mark containing the name, positional and keyword arguments.

    Attributes
    ----------
    name
        Name of the mark.
    args
        Positional arguments of the mark decorator.
    kwargs
        Keyword arguments of the mark decorator.

    """

    name: str
    args: tuple[Any, ...]
    kwargs: Mapping[str, Any]

    def combined_with(self, other: Mark) -> Mark:
        """Return a new Mark which is a combination of this Mark and another Mark.

        Combines by appending args and merging kwargs.

        Parameters
        ----------
        other
            The mark to combine with.

        Returns
        -------
        Mark
            The new mark which is a combination of two marks.

        """
        assert self.name == other.name
        return Mark(self.name, self.args + other.args, {**self.kwargs, **other.kwargs})


@define
class MarkDecorator:
    """A decorator for applying a mark on task function.

    Decorators are created with :class:`pytask.mark`.

    .. code-block:: python

        mark1 = pytask.mark.NAME  # Simple MarkDecorator
        mark2 = pytask.mark.NAME(name1=value)  # Parametrized MarkDecorator

    and can then be applied as decorators to task functions

    .. code-block:: python

        @mark2
        def task_function():
            pass

    When a :class:`MarkDecorator` is called it does the following:

    1. If called with a single function as its only positional argument and no
       additional keyword arguments, it attaches the mark to the function, containing
       all the arguments already stored internally in the :class:`MarkDecorator`.
    2. When called in any other case, it returns a new :class:`MarkDecorator` instance
       with the original :class:`MarkDecorator`'s content updated with the arguments
       passed to this call.

    Notes
    -----
    The rules above prevent decorators from storing only a single function or class
    reference as their positional argument with no additional keyword or positional
    arguments. You can work around this by using :meth:`MarkDecorator.with_args()`.

    """

    mark: Mark = field(validator=validators.instance_of(Mark))

    @property
    def name(self) -> str:
        """Alias for mark.name."""
        return self.mark.name

    @property
    def args(self) -> tuple[Any, ...]:
        """Alias for mark.args."""
        return self.mark.args

    @property
    def kwargs(self) -> Mapping[str, Any]:
        """Alias for mark.kwargs."""
        return self.mark.kwargs

    def __repr__(self) -> str:
        return f"<MarkDecorator {self.mark!r}>"

    def with_args(self, *args: Any, **kwargs: Any) -> MarkDecorator:
        """Return a MarkDecorator with extra arguments added.

        Unlike calling the MarkDecorator, ``with_args()`` can be used even if the sole
        argument is a callable.

        """
        mark = Mark(self.name, args, kwargs)
        return self.__class__(self.mark.combined_with(mark))

    def __call__(self, *args: Any, **kwargs: Any) -> MarkDecorator:
        """Call the MarkDecorator."""
        if args and not kwargs:
            func = args[0]
            if len(args) == 1 and is_task_function(func):
                store_mark(func, self.mark)
                return func
        return self.with_args(*args, **kwargs)


def get_unpacked_marks(obj: Callable[..., Any]) -> list[Mark]:
    """Obtain the unpacked marks that are stored on an object."""
    mark_list = get_all_marks(obj)
    return normalize_mark_list(mark_list)


def normalize_mark_list(mark_list: Iterable[Mark | MarkDecorator]) -> list[Mark]:
    """Normalize marker decorating helpers to mark objects.

    Parameters
    ----------
    mark_list : List[Union[Mark, MarkDecorator]]

    Returns
    -------
    List[Mark]

    """
    extracted = [getattr(mark, "mark", mark) for mark in mark_list]
    for mark in extracted:
        if not isinstance(mark, Mark):  # pragma: no cover
            msg = f"Got {mark!r} instead of Mark."
            raise TypeError(msg)
    return [x for x in extracted if isinstance(x, Mark)]


def store_mark(obj: Callable[..., Any], mark: Mark) -> None:
    """Store a Mark on an object.

    This is used to implement the Mark declarations/decorators correctly.

    """
    assert isinstance(mark, Mark), mark
    if hasattr(obj, "pytask_meta"):
        obj.pytask_meta.markers = [*get_unpacked_marks(obj), mark]
    else:
        obj.pytask_meta = CollectionMetadata(  # type: ignore[attr-defined]
            markers=[mark]
        )


_DEPRECATION_DECORATOR = """'@pytask.mark.{}' was removed in pytask v0.5.0. To upgrade \
your project to the new syntax, read the tutorial on product and dependencies: \
https://tinyurl.com/pytask-deps-prods.
"""


class MarkGenerator:
    """Factory for :class:`MarkDecorator` objects.

    Exposed as a :class:`pytask.mark` singleton instance.

    Example
    -------
    >>> import pytask

    >>> @pytask.mark.skip
    ... def task_function():
    ...    pass

    applies a 'skip' :class:`Mark` on ``task_function``.

    """

    config: dict[str, Any] | None = None
    """Optional[Dict[str, Any]]: The configuration."""

    def __getattr__(self, name: str) -> MarkDecorator | Any:
        if name[0] == "_":
            msg = "Marker name must NOT start with underscore"
            raise AttributeError(msg)

        if name in ("depends_on", "produces"):
            raise RuntimeError(_DEPRECATION_DECORATOR.format(name))

        if name == "task":
            msg = (
                "'@pytask.mark.task' is removed. Use '@task' with 'from pytask import "
                "task' instead."
            )
            raise RuntimeError(msg)

        # If the name is not in the set of known marks after updating,
        # then it really is time to issue a warning or an error.
        if self.config is not None and name not in self.config["markers"]:
            if name in ("parametrize", "parameterize", "parametrise", "parameterise"):
                msg = (
                    "@pytask.mark.parametrize has been removed since pytask v0.4. "
                    "Upgrade your parametrized tasks to the new syntax defined in "
                    "https://tinyurl.com/pytask-loops or revert to v0.3."
                )
                raise NotImplementedError(msg) from None

            if self.config["strict_markers"]:
                msg = f"Unknown pytask.mark.{name}."
                raise ValueError(msg)

            warnings.warn(
                f"Unknown pytask.mark.{name} - is this a typo? You can register "
                "custom marks to avoid this warning.",
                stacklevel=2,
            )

        return MarkDecorator(Mark(name, (), {}))


MARK_GEN = MarkGenerator()
