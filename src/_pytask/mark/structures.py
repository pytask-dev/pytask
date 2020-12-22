import warnings
from typing import Any
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import Union

import attr


def get_specific_markers_from_task(task, marker_name):
    return [marker for marker in task.markers if marker.name == marker_name]


def get_marks_from_obj(obj, marker_name):
    return [
        marker
        for marker in getattr(obj, "pytaskmark", [])
        if marker.name == marker_name
    ]


def has_marker(obj, marker_name):
    return any(marker.name == marker_name for marker in getattr(obj, "pytaskmark", []))


def is_task_function(func) -> bool:
    return callable(func) and getattr(func, "__name__", "<lambda>") != "<lambda>"


@attr.s(frozen=True)
class Mark:
    name = attr.ib(type=str)
    """str: Name of the mark."""
    args = attr.ib(type=Tuple[Any, ...])
    """Tuple[Any]: Positional arguments of the mark decorator."""
    kwargs = attr.ib(type=Mapping[str, Any])
    """Mapping[str, Any]: Keyword arguments of the mark decorator."""

    _param_ids_from = attr.ib(type=Optional["Mark"], default=None, repr=False)
    """Optional[Mark]: Source Mark for ids with parametrize Marks."""
    _param_ids_generated = attr.ib(
        type=Optional[Sequence[str]], default=None, repr=False
    )
    """Optional[Sequence[str]]: Resolved/generated ids with parametrize Marks."""

    def _has_param_ids(self) -> bool:
        return "ids" in self.kwargs or len(self.args) >= 4

    def combined_with(self, other: "Mark") -> "Mark":
        """Return a new Mark which is a combination of this Mark and another Mark.

        Combines by appending args and merging kwargs.

        Parameters
        ----------
        other : pytask.mark.structures.Mark
            The mark to combine with.

        Returns
        -------
        Mark
            The new mark which is a combination of two marks.

        """
        assert self.name == other.name

        # Remember source of ids with parametrize Marks.
        param_ids_from: Optional[Mark] = None
        if self.name == "parametrize":
            if other._has_param_ids():
                param_ids_from = other
            elif self._has_param_ids():
                param_ids_from = self

        return Mark(
            self.name,
            self.args + other.args,
            dict(self.kwargs, **other.kwargs),
            param_ids_from=param_ids_from,
        )


@attr.s
class MarkDecorator:
    """A decorator for applying a mark on task function.

    MarkDecorators are created with ``pytask.mark``

    .. code-block:: python

        mark1 = pytask.mark.NAME  # Simple MarkDecorator
        mark2 = pytask.mark.NAME(name1=value)  # Parametrized MarkDecorator

    and can then be applied as decorators to task functions

    .. code-block:: python

        @mark2
        def task_function():
            pass

    When a MarkDecorator is called it does the following:

    1. If called with a single function as its only positional argument and no
       additional keyword arguments, it attaches the mark to the function, containing
       all the arguments already stored internally in the MarkDecorator.
    2. When called in any other case, it returns a new MarkDecorator instance with the
       original MarkDecorator's content updated with the arguments passed to this call.

    Notes
    -----
    The rules above prevent MarkDecorators from storing only a single function or class
    reference as their positional argument with no additional keyword or positional
    arguments. You can work around this by using `with_args()`.

    """

    mark = attr.ib(type=Mark, validator=attr.validators.instance_of(Mark))

    @property
    def name(self) -> str:
        """Alias for mark.name."""
        return self.mark.name

    @property
    def args(self) -> Tuple[Any, ...]:
        """Alias for mark.args."""
        return self.mark.args

    @property
    def kwargs(self) -> Mapping[str, Any]:
        """Alias for mark.kwargs."""
        return self.mark.kwargs

    def __repr__(self) -> str:
        return f"<MarkDecorator {self.mark!r}>"

    def with_args(self, *args: object, **kwargs: object) -> "MarkDecorator":
        """Return a MarkDecorator with extra arguments added.

        Unlike calling the MarkDecorator, ``with_args()`` can be used even if the sole
        argument is a callable.

        """
        mark = Mark(self.name, args, kwargs)
        return self.__class__(self.mark.combined_with(mark))

    def __call__(self, *args: object, **kwargs: object):  # noqa: F811
        """Call the MarkDecorator."""
        if args and not kwargs:
            func = args[0]
            if len(args) == 1 and is_task_function(func):
                store_mark(func, self.mark)
                return func
        return self.with_args(*args, **kwargs)


def get_unpacked_marks(obj) -> List[Mark]:
    """Obtain the unpacked marks that are stored on an object."""
    mark_list = getattr(obj, "pytaskmark", [])
    if not isinstance(mark_list, list):
        mark_list = [mark_list]
    return normalize_mark_list(mark_list)


def normalize_mark_list(mark_list: Iterable[Union[Mark, MarkDecorator]]) -> List[Mark]:
    """Normalizes marker decorating helpers to mark objects.

    Parameters
    ----------
    mark_list : List[Union[Mark, MarkDecorator]]

    Returns
    -------
    List[Mark]

    """
    extracted = [
        getattr(mark, "mark", mark) for mark in mark_list
    ]  # unpack MarkDecorator
    for mark in extracted:
        if not isinstance(mark, Mark):
            raise TypeError(f"got {mark!r} instead of Mark")
    return [x for x in extracted if isinstance(x, Mark)]


def store_mark(obj, mark: Mark) -> None:
    """Store a Mark on an object.
    This is used to implement the Mark declarations/decorators correctly.
    """
    assert isinstance(mark, Mark), mark
    # Always reassign name to avoid updating pytaskmark in a reference that
    # was only borrowed.
    obj.pytaskmark = get_unpacked_marks(obj) + [mark]


class MarkGenerator:
    """Factory for :class:`MarkDecorator` objects - exposed as a ``pytask.mark``
    singleton instance.

    Example
    -------
    >>> import pytask

    >>> @pytask.mark.skip
    ... def task_function():
    ...    pass

    applies a 'skip' :class:`Mark` on ``task_function``.

    """

    config = None
    """Optional[dict]: The configuration."""
    markers = set()
    """Set[str]: The set of markers."""

    def __getattr__(self, name: str) -> MarkDecorator:
        if name[0] == "_":
            raise AttributeError("Marker name must NOT start with underscore")

        if self.config is not None:
            # We store a set of markers as a performance optimization - if a mark
            # name is in the set we definitely know it, but a mark may be known and
            # not in the set.  We therefore start by updating the set!
            if name not in self.markers:
                self.markers.update(self.config["markers"])

            # If the name is not in the set of known marks after updating,
            # then it really is time to issue a warning or an error.
            if name not in self.markers:
                if self.config["strict_markers"]:
                    raise ValueError(f"Unknown pytask.mark.{name}.")
                # Raise a specific error for common misspellings of "parametrize".
                if name in ["parameterize", "parametrise", "parameterise"]:
                    warnings.warn(f"Unknown '{name}' mark, did you mean 'parametrize'?")

                warnings.warn(
                    f"Unknown pytask.mark.{name} - is this a typo? You can register "
                    "custom marks to avoid this warning.",
                    stacklevel=2,
                )

        return MarkDecorator(Mark(name, (), {}))


MARK_GEN = MarkGenerator()
