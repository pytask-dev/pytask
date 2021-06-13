import copy
import functools
import itertools
import pprint
import types
from typing import Any
from typing import Callable
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from _pytask.config import hookimpl
from _pytask.console import format_strings_as_flat_tree
from _pytask.console import TASK_ICON
from _pytask.mark import Mark
from _pytask.mark import MARK_GEN as mark  # noqa: N811
from _pytask.shared import find_duplicates


def parametrize(
    arg_names: Union[str, Tuple[str], List[str]],
    arg_values: Iterable,
    *,
    ids: Optional[
        Union[Iterable[Union[bool, float, int, str, None]], Callable[[Any], Any]]
    ] = None,
):
    """Parametrize a task function.

    Parametrizing a task allows to execute the same task with different arguments.

    Parameters
    ----------
    arg_names : Union[str, Tuple[str], List[str]]
        The names of the arguments which can either be given as a comma-separated
        string, a tuple of strings, or a list of strings.
    arg_values : Iterable
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
def pytask_parse_config(config):
    config["markers"]["parametrize"] = (
        "Call a task function multiple times passing in different arguments each turn. "
        "arg_values generally needs to be a list of values if arg_names specifies only "
        "one name or a list of tuples of values if arg_names specifies multiple "
        "names.Example: @pytask.mark.parametrize('arg1', [1, 2]) would lead to two "
        "calls of the decorated task function, one with arg1=1 and another with arg1=2."
        " See this [link https://bit.ly/3vqyiAk]tutorial (https://bit.ly/3vqyiAk)[/] "
        "for more info and examples."
    )


@hookimpl
def pytask_parametrize_task(session, name, obj):
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
        obj, markers = _remove_parametrize_markers_from_func(obj)

        if len(markers) > 1:
            raise NotImplementedError(
                "Multiple parametrizations are currently not implemented since it is "
                "not possible to define products for tasks from a cartesian product."
            )

        base_arg_names, arg_names, arg_values = _parse_parametrize_markers(
            markers, name
        )

        product_arg_names = list(itertools.product(*arg_names))
        product_arg_values = list(itertools.product(*arg_values))

        names_and_functions = []
        for names, values in zip(product_arg_names, product_arg_values):
            kwargs = dict(
                zip(
                    itertools.chain.from_iterable(base_arg_names),
                    itertools.chain.from_iterable(values),
                )
            )

            # Copy function and attributes to allow in-place changes.
            func = _copy_func(obj)
            func.pytaskmark = copy.deepcopy(obj.pytaskmark)

            # Convert parametrized dependencies and products to decorator.
            session.hook.pytask_parametrize_kwarg_to_marker(obj=func, kwargs=kwargs)

            # Attach remaining parametrized arguments to the function.
            partialed_func = functools.partial(func, **kwargs)
            wrapped_func = functools.update_wrapper(partialed_func, func)

            name_ = f"{name}[{'-'.join(itertools.chain.from_iterable(names))}]"
            names_and_functions.append((name_, wrapped_func))

        names = [i[0] for i in names_and_functions]
        duplicates = find_duplicates(names)
        if duplicates:
            text = format_strings_as_flat_tree(
                duplicates, "Duplicated task ids", TASK_ICON
            )
            raise ValueError(
                "The following ids are duplicated while parametrizing task "
                f"'{obj.__name__}'.\n\n{text}\n\nIt might be caused by "
                "parametrizing the task with the same combination of arguments "
                "multiple times. Change the arguments or change the ids generated by "
                "the parametrization."
            )

        return names_and_functions


def _remove_parametrize_markers_from_func(obj):
    """Remove parametrize markers from the object."""
    parametrize_markers = [i for i in obj.pytaskmark if i.name == "parametrize"]
    others = [i for i in obj.pytaskmark if i.name != "parametrize"]
    obj.pytaskmark = others

    return obj, parametrize_markers


def _parse_parametrize_marker(marker: Mark, name: str) -> Tuple[Any, Any, Any]:
    """Parse parametrize marker.

    Parameters
    ----------
    marker : Mark
        A parametrize mark.
    name : str
        The name of the task function which is parametrized.

    Returns
    -------
    base_arg_names : Tuple[str]
        Contains the names of the arguments.
    processed_arg_names : List[Tuple[str]]
        Each tuple in the list represents the processed names of the arguments suffixed
        with a number indicating the iteration.
    processed_arg_values : List[Tuple[Any]]
        Each tuple in the list represents the values of the arguments for each
        iteration.

    """
    arg_names, arg_values, ids = parametrize(*marker.args, **marker.kwargs)

    parsed_arg_names = _parse_arg_names(arg_names)
    parsed_arg_values = _parse_arg_values(arg_values)

    _check_if_n_arg_names_matches_n_arg_values(
        parsed_arg_names, parsed_arg_values, name
    )

    expanded_arg_names = _create_parametrize_ids_components(
        parsed_arg_names, parsed_arg_values, ids
    )

    return parsed_arg_names, expanded_arg_names, parsed_arg_values


def _parse_parametrize_markers(markers: List[Mark], name: str):
    """Parse parametrize markers."""
    parsed_markers = [_parse_parametrize_marker(marker, name) for marker in markers]
    base_arg_names = [i[0] for i in parsed_markers]
    processed_arg_names = [i[1] for i in parsed_markers]
    processed_arg_values = [i[2] for i in parsed_markers]

    return base_arg_names, processed_arg_names, processed_arg_values


def _parse_arg_names(arg_names: Union[str, Tuple[str], List[str]]) -> Tuple[str]:
    """Parse arg_names argument of parametrize decorator.

    There are three allowed formats:

    1. comma-separated string representation.
    2. a tuple of strings.
    3. a list of strings.

    All formats are converted to a tuple of strings.

    Parameters
    ----------
    arg_names : Union[str, Tuple[str], List[str]]
        The names of the arguments which are parametrized.

    Returns
    -------
    out : Tuple[str]
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
        raise ValueError(
            "The argument 'arg_names' accepts comma-separated strings, tuples and lists"
            f" of strings. It cannot accept {arg_names} with type {type(arg_names)}."
        )

    return out


def _parse_arg_values(arg_values: Iterable) -> List[Tuple[Any]]:
    """Parse the values provided for each argument name.

    Example
    -------
    >>> _parse_arg_values(["a", "b", "c"])
    [('a',), ('b',), ('c',)]
    >>> _parse_arg_values([(0, 0), (0, 1), (1, 0)])
    [(0, 0), (0, 1), (1, 0)]

    """
    return [
        tuple(i) if isinstance(i, Iterable) and not isinstance(i, str) else (i,)
        for i in arg_values
    ]


def _check_if_n_arg_names_matches_n_arg_values(
    arg_names: Tuple[str], arg_values: List[Tuple[Any]], name: str
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
            f"Task '{name}' is parametrized with {n_names} 'arg_names', {arg_names}, "
            f"but the number of provided 'arg_values' is {pretty_arg_values}. For "
            f"example, here are the values of parametrization no. {idx_example}:"
            f"\n\n{formatted_example}"
        )


def _create_parametrize_ids_components(
    arg_names: Tuple[str],
    arg_values: List[Tuple[Any]],
    ids: Optional[
        Union[Iterable[Union[bool, float, int, str, None]], Callable[[Any], Any]]
    ],
):
    """Create the ids for each parametrization.

    Parameters
    ----------
    arg_names : Tuple[str]
        The names of the arguments of the parametrized function.
    arg_values : List[Tuple[Any]]
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
        parsed_ids = [(id_,) for id_ in ids]

        if len(parsed_ids) != len(arg_values):
            raise ValueError("The number of ids must match the number of runs.")

        if not all(
            isinstance(id_, (bool, int, float, str)) or id_ is None
            for id_ in itertools.chain.from_iterable(parsed_ids)
        ):
            raise ValueError(
                "Ids for parametrization can only be of type bool, float, int, str or "
                "None."
            )

        parsed_ids = [(str(id_),) for id_ in itertools.chain.from_iterable(parsed_ids)]

    else:
        parsed_ids = []
        for i, _arg_values in enumerate(arg_values):
            id_components = tuple(
                _arg_value_to_id_component(arg_names[j], arg_value, i, ids)
                for j, arg_value in enumerate(_arg_values)
            )
            parsed_ids.append(id_components)

    return parsed_ids


def _arg_value_to_id_component(
    arg_name: str, arg_value: Any, i: int, id_func: Union[Callable[[Any], Any], None]
) -> str:
    """Create id component from the name and value of the argument.

    First, transform the value of the argument with a user-defined function if given.
    Otherwise, take the original value. Then, if the value is a :obj:`bool`,
    :obj:`float`, :obj:`int`, or :obj:`str`, cast it to a string. Otherwise, define a
    placeholder value from the name of the argument and the iteration.

    Parameters
    ----------
    arg_name : str
        Name of the parametrized function argument.
    arg_value : Any
        Value of the argument.
    i : int
        The ith iteration of the parametrization.
    id_func : Union[Callable[[Any], Any], None]
        A callable which maps argument values to :obj:`bool`, :obj:`float`, :obj:`int`,
        or :obj:`str` or anything else. Any object with a different dtype than the first
        will be mapped to an auto-generated id component.

    Returns
    -------
    id_component : str
        A part of the final parametrized id.

    """
    id_component = id_func(arg_value) if id_func is not None else None
    if isinstance(id_component, (bool, float, int, str)):
        id_component = str(id_component)
    elif isinstance(arg_value, (bool, float, int, str)):
        id_component = str(arg_value)
    else:
        id_component = arg_name + str(i)
    return id_component


@hookimpl
def pytask_parametrize_kwarg_to_marker(obj, kwargs: dict) -> None:
    """Add some parametrized keyword arguments as decorator."""
    if callable(obj):
        for marker_name in ["depends_on", "produces"]:
            if marker_name in kwargs:
                mark.__getattr__(marker_name)(kwargs.pop(marker_name))(obj)


def _copy_func(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
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
