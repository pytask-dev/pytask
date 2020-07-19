import copy
import functools
import inspect
import itertools
import types
from collections.abc import Iterable

import pytask
from pytask.mark import Mark


def parametrize(argnames, argvalues):
    """Parametrize task function.

    Parameters
    ----------
    argnames : str, tuple of str, list of str
        The names of the arguments.
    argvalues : list, list of iterables
        The values which correspond to names in ``argnames``.

    This functions is more a helper function to parse the arguments of the decorator and
    to document the marker than a real function.

    """
    return argnames, argvalues


@pytask.hookimpl
def pytask_generate_tasks(name, obj):
    if callable(obj):
        obj, markers = _remove_parametrize_markers_from_func(obj)
        base_arg_names, arg_names, arg_values = _parse_parametrize_markers(markers)

        diff_arg_names = (
            set(itertools.chain.from_iterable(base_arg_names))
            - set(inspect.getfullargspec(obj).args)
            - {"depends_on", "produces"}
        )
        if diff_arg_names:
            raise ValueError(
                f"Parametrized function '{name}' does not have the following "
                f"parametrized arguments: {diff_arg_names}."
            )

        names_and_functions = _generate_product_of_names_and_functions(
            name, obj, base_arg_names, arg_names, arg_values
        )

        return names_and_functions


def _remove_parametrize_markers_from_func(obj):
    parametrize = [i for i in obj.pytestmark if i.name == "parametrize"]
    others = [i for i in obj.pytestmark if i.name != "parametrize"]
    obj.pytestmark = others

    return obj, parametrize


def _parse_parametrize_markers(markers):
    base_arg_names = []
    processed_arg_names = []
    processed_arg_values = []

    for marker in markers:
        arg_names, arg_values = parametrize(*marker.args, **marker.kwargs)

        parsed_arg_names = _parse_arg_names(arg_names)
        parsed_arg_values = _parse_arg_values(arg_values)

        n_runs = len(parsed_arg_values)

        expanded_arg_names = _expand_arg_names(parsed_arg_names, n_runs)

        base_arg_names.append(parsed_arg_names)
        processed_arg_names.append(expanded_arg_names)
        processed_arg_values.append(parsed_arg_values)

    return base_arg_names, processed_arg_names, processed_arg_values


def _parse_arg_names(argnames):
    """Parse argnames argument of parametrize decorator.

    Parameters
    ----------
    argnames : str, tuple of str, list or str
        The names of the arguments which are parametrized.

    Returns
    -------
    out : str, tuples of str
        The parse argnames.

    Example
    -------
    >>> _parse_arg_names("i")
    ('i',)
    >>> _parse_arg_names("i, j")
    ('i', 'j')

    """
    if isinstance(argnames, str):
        out = tuple(i.strip() for i in argnames.split(","))
    elif isinstance(argnames, (tuple, list)):
        out = tuple(argnames)

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


def _expand_arg_names(argnames, n_runs):
    """Expands the names of the arguments for each run.

    Parameters
    ----------
    argnames : str, list of str
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
    return [tuple(name + str(i) for name in argnames) for i in range(n_runs)]


def _generate_product_of_names_and_functions(
    name, obj, base_arg_names, arg_names, arg_values
):
    names_and_functions = []
    product_arg_names = list(itertools.product(*arg_names))
    product_arg_values = list(itertools.product(*arg_values))

    for names, values in zip(product_arg_names, product_arg_values):
        kwargs = dict(
            zip(
                itertools.chain.from_iterable(base_arg_names),
                itertools.chain.from_iterable(values),
            )
        )

        # Convert parametrized dependencies and products to decorator.
        func = _copy_func(obj)
        func.pytestmark = copy.deepcopy(obj.pytestmark)

        for marker_name in ["depends_on", "produces"]:
            if marker_name in kwargs:
                func.pytestmark.append(
                    Mark(marker_name, _to_tuple(kwargs.pop(marker_name)), {})
                )

        # Attach remaining parametrized arguments to the function.
        partialed_func = functools.partial(func, **kwargs)
        wrapped_func = functools.update_wrapper(partialed_func, func)

        name_ = f"{name}[{'-'.join(itertools.chain.from_iterable(names))}]"
        names_and_functions.append((name_, wrapped_func))

    return names_and_functions


def _to_tuple(x):
    return (x,) if not isinstance(x, Iterable) or isinstance(x, str) else tuple(x)


def _copy_func(f):
    """Based on https://stackoverflow.com/a/13503277/7523785."""
    g = types.FunctionType(
        f.__code__,
        f.__globals__,
        name=f.__name__,
        argdefs=f.__defaults__,
        closure=f.__closure__,
    )
    g = functools.update_wrapper(g, f)
    g.__kwdefaults__ = f.__kwdefaults__
    return g
