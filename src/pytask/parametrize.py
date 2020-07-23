import copy
import functools
import itertools
import types
from collections.abc import Iterable

import pytask


def parametrize(arg_names, arg_values):
    """Parametrize task function.

    Parameters
    ----------
    arg_names : str, tuple of str, list of str
        The names of the arguments.
    arg_values : iterable
        The values which correspond to names in ``arg_names``.

    This functions is more a helper function to parse the arguments of the decorator and
    to document the marker than a real function.

    """
    return arg_names, arg_values


@pytask.hookimpl
def pytask_parametrize_task(session, name, obj):
    """Parametrize a task.

    This function takes a single Python function and all parametrize decorators and
    generates multiple instances of the same task with different arguments.

    Note that, while a single ``@pytask.mark.parametrize`` is handled like a loop or a
    :func:`zip`, multiple ``@pytask.mark.parametrize`` decorators form a Cartesian
    product.

    """
    if callable(obj):
        obj, markers = _remove_parametrize_markers_from_func(obj)
        base_arg_names, arg_names, arg_values = _parse_parametrize_markers(markers)

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
            func.pytestmark = copy.deepcopy(obj.pytestmark)

            # Convert parametrized dependencies and products to decorator.
            session.hook.pytask_parametrize_kwarg_to_marker(obj=func, kwargs=kwargs)
            # Attach remaining parametrized arguments to the function.
            partialed_func = functools.partial(func, **kwargs)
            wrapped_func = functools.update_wrapper(partialed_func, func)

            name_ = f"{name}[{'-'.join(itertools.chain.from_iterable(names))}]"
            names_and_functions.append((name_, wrapped_func))

        return names_and_functions


def _remove_parametrize_markers_from_func(obj):
    parametrize = [i for i in obj.pytestmark if i.name == "parametrize"]
    others = [i for i in obj.pytestmark if i.name != "parametrize"]
    obj.pytestmark = others

    return obj, parametrize


def _parse_parametrize_marker(marker):
    """Parse parametrize marker.

    Parameters
    ----------
    marker : pytask.mark.Mark
        A parametrize mark.

    Returns
    -------
    base_arg_names : tuple of str
        Contains the names of the arguments.
    processed_arg_names : list of tuple of str
        Each tuple in the list represents the processed names of the arguments suffixed
        with a number indicating the iteration.
    processed_arg_values : list of tuple of obj
        Each tuple in the list represents the values of the arguments for each
        iteration.

    """
    arg_names, arg_values = parametrize(*marker.args, **marker.kwargs)

    parsed_arg_names = _parse_arg_names(arg_names)
    parsed_arg_values = _parse_arg_values(arg_values)

    n_runs = len(parsed_arg_values)

    expanded_arg_names = _expand_arg_names(parsed_arg_names, n_runs)

    return parsed_arg_names, expanded_arg_names, parsed_arg_values


def _parse_parametrize_markers(markers):
    """Parse parametrize markers."""
    parsed_markers = [_parse_parametrize_marker(marker) for marker in markers]
    base_arg_names = [i[0] for i in parsed_markers]
    processed_arg_names = [i[1] for i in parsed_markers]
    processed_arg_values = [i[2] for i in parsed_markers]

    return base_arg_names, processed_arg_names, processed_arg_values


def _parse_arg_names(arg_names):
    """Parse arg_names argument of parametrize decorator.

    Parameters
    ----------
    arg_names : str, tuple of str, list or str
        The names of the arguments which are parametrized.

    Returns
    -------
    out : str, tuples of str
        The parse arg_names.

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

    return out


def _parse_arg_values(arg_values):
    """Parse the values provided for each argument name.

    Example
    -------
    >>> _parse_arg_values(["a", "b", "c"])
    [('a',), ('b',), ('c',)]
    >>> _parse_arg_values([(0, 0), (0, 1), (1, 0)])
    [(0, 0), (0, 1), (1, 0)]

    """
    return [
        i if isinstance(i, Iterable) and not isinstance(i, str) else (i,)
        for i in arg_values
    ]


def _expand_arg_names(arg_names, n_runs):
    """Expands the names of the arguments for each run.

    Parameters
    ----------
    arg_names : str, list of str
        The names of the arguments of the parametrized function.
    n_runs : int
        How many argument values are passed to the function.

    Examples
    --------
    >>> _expand_arg_names(["i"], 2)
    [('i0',), ('i1',)]

    >>> _expand_arg_names(["i", "j"], 2)
    [('i0', 'j0'), ('i1', 'j1')]

    """
    return [tuple(name + str(i) for name in arg_names) for i in range(n_runs)]


@pytask.hookimpl
def pytask_parametrize_kwarg_to_marker(obj, kwargs):
    """Add some parametrized keyword arguments as decorator."""
    if callable(obj):
        for marker_name in ["depends_on", "produces"]:
            if marker_name in kwargs:
                pytask.mark.__getattr__(marker_name)(kwargs.pop(marker_name))(obj)


def _to_tuple(x):
    """Convert object to tuple.

    Example
    -------
    >>> _to_tuple(list("ab"))
    ('a', 'b')
    >>> _to_tuple("a")
    ('a',)
    >>> _to_tuple("ab")
    ('ab',)

    """
    return (x,) if not isinstance(x, Iterable) or isinstance(x, str) else tuple(x)


def _copy_func(func):
    """Create a copy of a function.

    Based on https://stackoverflow.com/a/13503277/7523785.

    Example
    -------
    >>> def func(): pass
    >>> copied_func = _copy_func(func)
    >>> func == copied_func
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
