from __future__ import annotations

import copy
import functools
import itertools
import pprint
import types
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Sequence

from _pytask.config import hookimpl
from _pytask.console import format_strings_as_flat_tree
from _pytask.console import TASK_ICON
from _pytask.mark import Mark
from _pytask.mark import MARK_GEN as mark  # noqa: N811
from _pytask.mark_utils import remove_marks
from _pytask.parametrize_utils import arg_value_to_id_component
from _pytask.session import Session
from _pytask.shared import find_duplicates


def parametrize(
    arg_names: str | list[str] | tuple[str, ...],
    arg_values: Iterable[Sequence[Any] | Any],
    *,
    ids: None | (Iterable[None | str | float | int | bool] | Callable[..., Any]) = None,
) -> tuple[
    str | list[str] | tuple[str, ...],
    Iterable[Sequence[Any] | Any],
    Iterable[None | str | float | int | bool] | Callable[..., Any] | None,
]:
    """Parametrize a task function.

    Parametrizing a task allows to execute the same task with different arguments.

    Parameters
    ----------
    arg_names : str | list[str] | tuple[str, ...]
        The names of the arguments which can either be given as a comma-separated
        string, a tuple of strings, or a list of strings.
    arg_values : Iterable[Sequence[Any] | Any]
        The values which correspond to names in ``arg_names``. For one argument, it is a
        single iterable. For multiple argument names it is an iterable of iterables.
    ids
        This argument can either be a list with ids or a function which is called with
        every value passed to the parametrized function.

        If you pass an iterable with ids, make sure to only use :obj:`bool`,
        :obj:`float`, :obj:`int`, or :obj:`str` as values which are used to create task
        ids like ``"task_dummpy.py::task_dummy[first_task_id]"``.

        If you pass a function, the function receives each value of the parametrization
        and may return a boolean, number, string or None. For the latter, the
        auto-generated value is used.

    """
    return arg_names, arg_values, ids


@hookimpl
def pytask_parse_config(config: dict[str, Any]) -> None:
    config["markers"]["parametrize"] = (
        "The marker for pytest's way of repeating tasks which is explained in this "
        "tutorial: [link https://bit.ly/3uqZqkk]https://bit.ly/3uqZqkk[/]."
    )


@hookimpl
def pytask_parametrize_task(
    session: Session, name: str, obj: Callable[..., Any]
) -> list[tuple[str, Callable[..., Any]]]:
    """Parametrize a task.

    This function takes a single Python function and all parametrize decorators and
    generates multiple instances of the same task with different arguments.

    Note that, while a single ``@pytask.mark.parametrize`` is handled like a loop or a
    :func:`zip`, multiple ``@pytask.mark.parametrize`` decorators form a Cartesian
    product.

    We cannot raise an error if the function does not use parametrized arguments since
    some plugins will replace functions with their own implementation like pytask-r.

    """
    if callable(obj):
        obj, markers = remove_marks(obj, "parametrize")  # type: ignore

        if len(markers) > 1:
            raise NotImplementedError(
                "You cannot apply @pytask.mark.parametrize multiple times to a task. "
                "Use multiple for-loops, itertools.product or a different strategy to "
                "create all combinations of inputs and pass it to a single "
                "@pytask.mark.parametrize.\n\nFor improved readability, consider to "
                "move the creation of inputs into its own function as shown in the "
                "best-practices guide on parametrizations: https://pytask-dev.rtfd.io/"
                "en/stable/how_to_guides/bp_scalable_repititions_of_tasks.html."
            )

        base_arg_names, arg_names, arg_values = _parse_parametrize_markers(
            markers, name
        )

        product_arg_names = list(itertools.product(*arg_names))
        product_arg_values = list(itertools.product(*arg_values))

        names_and_functions: list[tuple[str, Callable[..., Any]]] = []
        for names, values in zip(product_arg_names, product_arg_values):
            kwargs = dict(
                zip(
                    itertools.chain.from_iterable(base_arg_names),
                    itertools.chain.from_iterable(values),
                )
            )

            # Copy function and attributes to allow in-place changes.
            func = _copy_func(obj)  # type: ignore
            func.pytask_meta = copy.deepcopy(  # type: ignore[attr-defined]
                obj.pytask_meta  # type: ignore[attr-defined]
            )
            # Convert parametrized dependencies and products to decorator.
            session.hook.pytask_parametrize_kwarg_to_marker(obj=func, kwargs=kwargs)

            func.pytask_meta.kwargs = {  # type: ignore[attr-defined]
                **func.pytask_meta.kwargs,  # type: ignore[attr-defined]
                **kwargs,
            }

            name_ = f"{name}[{'-'.join(itertools.chain.from_iterable(names))}]"
            names_and_functions.append((name_, func))

        all_names = [i[0] for i in names_and_functions]
        duplicates = find_duplicates(all_names)

        if duplicates:
            text = format_strings_as_flat_tree(
                duplicates, "Duplicated task ids", TASK_ICON
            )
            raise ValueError(
                "The following ids are duplicated while parametrizing task "
                f"{name!r}.\n\n{text}\n\nIt might be caused by "
                "parametrizing the task with the same combination of arguments "
                "multiple times. Change the arguments or change the ids generated by "
                "the parametrization."
            )

        return names_and_functions


def _parse_parametrize_marker(
    marker: Mark, name: str
) -> tuple[tuple[str, ...], list[tuple[str, ...]], list[tuple[Any, ...]]]:
    """Parse parametrize marker.

    Parameters
    ----------
    marker : Mark
        A parametrize mark.
    name : str
        The name of the task function which is parametrized.

    Returns
    -------
    base_arg_names : Tuple[str, ...]
        Contains the names of the arguments.
    processed_arg_names : List[Tuple[str, ...]]
        Each tuple in the list represents the processed names of the arguments suffixed
        with a number indicating the iteration.
    processed_arg_values : List[Tuple[Any, ...]]
        Each tuple in the list represents the values of the arguments for each
        iteration.

    """
    arg_names, arg_values, ids = parametrize(*marker.args, **marker.kwargs)

    parsed_arg_names = _parse_arg_names(arg_names)
    has_single_arg = len(parsed_arg_names) == 1
    parsed_arg_values = _parse_arg_values(arg_values, has_single_arg)

    _check_if_n_arg_names_matches_n_arg_values(
        parsed_arg_names, parsed_arg_values, name
    )

    expanded_arg_names = _create_parametrize_ids_components(
        parsed_arg_names, parsed_arg_values, ids
    )

    return parsed_arg_names, expanded_arg_names, parsed_arg_values


def _parse_parametrize_markers(
    markers: list[Mark], name: str
) -> tuple[
    list[tuple[str, ...]],
    list[list[tuple[str, ...]]],
    list[list[tuple[Any, ...]]],
]:
    """Parse parametrize markers."""
    parsed_markers = [_parse_parametrize_marker(marker, name) for marker in markers]
    base_arg_names = [i[0] for i in parsed_markers]
    processed_arg_names = [i[1] for i in parsed_markers]
    processed_arg_values = [i[2] for i in parsed_markers]

    return base_arg_names, processed_arg_names, processed_arg_values


def _parse_arg_names(arg_names: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Parse arg_names argument of parametrize decorator.

    There are three allowed formats:

    1. comma-separated string representation.
    2. a tuple of strings.
    3. a list of strings.

    All formats are converted to a tuple of strings.

    Parameters
    ----------
    arg_names : Union[str, List[str], Tuple[str, ...]]
        The names of the arguments which are parametrized.

    Returns
    -------
    out : Tuple[str, ...]
        The parsed arg_names.

    Example
    -------
    >>> _parse_arg_names("i")
    ('i',)
    >>> _parse_arg_names("i, j")
    ('i', 'j')

    """
    if isinstance(arg_names, str):
        out = tuple(i.strip() for i in arg_names.split(","))
    elif isinstance(arg_names, (tuple, list)):
        out = tuple(arg_names)
    else:
        raise TypeError(
            "The argument 'arg_names' accepts comma-separated strings, tuples and lists"
            f" of strings. It cannot accept {arg_names} with type {type(arg_names)}."
        )

    return out


def _parse_arg_values(
    arg_values: Iterable[Sequence[Any] | Any], has_single_arg: bool
) -> list[tuple[Any, ...]]:
    """Parse the values provided for each argument name.

    After processing the values, the return is a list where each value is an iteration
    of the parametrization. Each iteration is a tuple of all parametrized arguments.

    Example
    -------
    >>> _parse_arg_values(["a", "b", "c"], has_single_arg=True)
    [('a',), ('b',), ('c',)]
    >>> _parse_arg_values([(0, 0), (0, 1), (1, 0)], has_single_arg=False)
    [(0, 0), (0, 1), (1, 0)]

    """
    return [
        tuple(i)
        if isinstance(i, Iterable)
        and not isinstance(i, str)
        and not (isinstance(i, dict) and has_single_arg)
        else (i,)
        for i in arg_values
    ]


def _check_if_n_arg_names_matches_n_arg_values(
    arg_names: tuple[str, ...], arg_values: list[tuple[Any, ...]], name: str
) -> None:
    """Check if the number of argument names matches the number of arguments."""
    n_names = len(arg_names)
    n_values = [len(i) for i in arg_values]
    unique_n_values = tuple(set(n_values))

    if not all(i == n_names for i in unique_n_values):
        pretty_arg_values = (
            f"{unique_n_values[0]}"
            if len(unique_n_values) == 1
            else " or ".join(map(str, unique_n_values))
        )
        idx_example = [i == n_names for i in n_values].index(False)
        formatted_example = pprint.pformat(arg_values[idx_example])
        raise ValueError(
            f"Task {name!r} is parametrized with {n_names} 'arg_names', {arg_names}, "
            f"but the number of provided 'arg_values' is {pretty_arg_values}. For "
            f"example, here are the values of parametrization no. {idx_example}:"
            f"\n\n{formatted_example}"
        )


def _create_parametrize_ids_components(
    arg_names: tuple[str, ...],
    arg_values: list[tuple[Any, ...]],
    ids: None | (Iterable[None | str | float | int | bool] | Callable[..., Any]),
) -> list[tuple[str, ...]]:
    """Create the ids for each parametrization.

    Parameters
    ----------
    arg_names : Tuple[str, ...]
        The names of the arguments of the parametrized function.
    arg_values : List[Tuple[Any, ...]]
        A list of tuples where each tuple is for one run.
    ids
        The ids associated with one parametrization.

    Examples
    --------
    >>> _create_parametrize_ids_components(["i"], [(0,), (1,)], None)
    [('0',), ('1',)]

    >>> _create_parametrize_ids_components(["i", "j"], [(0, (0,)), (1, (1,))], None)
    [('0', 'j0'), ('1', 'j1')]

    """
    if isinstance(ids, Iterable):
        raw_ids = [(id_,) for id_ in ids]

        if len(raw_ids) != len(arg_values):
            raise ValueError("The number of ids must match the number of runs.")

        if not all(
            isinstance(id_, (bool, int, float, str)) or id_ is None
            for id_ in itertools.chain.from_iterable(raw_ids)
        ):
            raise ValueError(
                "Ids for parametrization can only be of type bool, float, int, str or "
                "None."
            )

        parsed_ids: list[tuple[str, ...]] = [
            (str(id_),) for id_ in itertools.chain.from_iterable(raw_ids)
        ]

    else:
        parsed_ids = []
        for i, _arg_values in enumerate(arg_values):
            id_components = tuple(
                arg_value_to_id_component(arg_names[j], arg_value, i, ids)
                for j, arg_value in enumerate(_arg_values)
            )
            parsed_ids.append(id_components)

    return parsed_ids


@hookimpl
def pytask_parametrize_kwarg_to_marker(obj: Any, kwargs: dict[str, str]) -> None:
    """Add some parametrized keyword arguments as decorator."""
    if callable(obj):
        for marker_name in ("depends_on", "produces"):
            if marker_name in kwargs:
                mark.__getattr__(marker_name)(kwargs.pop(marker_name))(obj)


def _copy_func(func: types.FunctionType) -> types.FunctionType:
    """Create a copy of a function.

    Based on https://stackoverflow.com/a/13503277/7523785.

    Example
    -------
    >>> def _func(): pass
    >>> copied_func = _copy_func(_func)
    >>> _func is copied_func
    False

    """
    new_func = types.FunctionType(
        func.__code__,
        func.__globals__,
        name=func.__name__,
        argdefs=func.__defaults__,
        closure=func.__closure__,
    )
    new_func = functools.update_wrapper(new_func, func)
    new_func.__kwdefaults__ = func.__kwdefaults__
    return new_func
