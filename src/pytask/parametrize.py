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
def pytask_parse_config(config):
    config["markers"]["parametrize"] = (
        "Call a task function multiple times passing in different arguments in turn. "
        "arg_values generally needs to be a list of values if arg_names specifies only "
        "one name or a list of tuples of values if arg_names specifies multiple "
        "names.Example: @pytask.mark.parametrize('arg1', [1,2]) would lead to two "
        "calls of the decorated task function, one with arg1=1 and another with "
        "arg1=2. See https://pytask-dev.rtfd.io/en/latest/tutorials/"
        "how_to_parametrize_a_task.html for more info and examples."
    )


@pytask.hookimpl
def pytask_generate_tasks(session, name, obj):
    if callable(obj):
        obj, markers = _remove_parametrize_markers_from_func(obj)
        base_arg_names, arg_names, arg_values = _parse_parametrize_markers(markers)

        names_and_functions = session.hook.generate_product_of_names_and_functions(
            session=session,
            name=name,
            obj=obj,
            base_arg_names=base_arg_names,
            arg_names=arg_names,
            arg_values=arg_values,
        )

        return names_and_functions


def _remove_parametrize_markers_from_func(obj):
    parametrize = [i for i in obj.pytaskmark if i.name == "parametrize"]
    others = [i for i in obj.pytaskmark if i.name != "parametrize"]
    obj.pytaskmark = others

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
def generate_product_of_names_and_functions(
    session, name, obj, base_arg_names, arg_names, arg_values
):
    """Generate product of names and functions.

    This function takes all ``@pytask.mark.parametrize`` decorators applied to a
    function and generates all combinations of parametrized arguments.

    Note that, while a single :func:`parametrize` is handled like a loop or a
    :func:`zip`, two :func:`parametrize` decorators form a Cartesian product.

    """
    if callable(obj):
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

            # Copy function and attributes to allow in-place changes.
            func = _copy_func(obj)
            func.pytaskmark = copy.deepcopy(obj.pytaskmark)

            # Convert parametrized dependencies and products to decorator.
            session.hook.pytask_generate_tasks_add_marker(obj=func, kwargs=kwargs)
            # Attach remaining parametrized arguments to the function.
            partialed_func = functools.partial(func, **kwargs)
            wrapped_func = functools.update_wrapper(partialed_func, func)

            name_ = f"{name}[{'-'.join(itertools.chain.from_iterable(names))}]"
            names_and_functions.append((name_, wrapped_func))

        return names_and_functions


@pytask.hookimpl
def pytask_generate_tasks_add_marker(obj, kwargs):
    """Add some parametrized keyword arguments as decorator."""
    if callable(obj):
        for marker_name in ["depends_on", "produces"]:
            if marker_name in kwargs:
                pytask.mark.__getattr__(marker_name)(kwargs.pop(marker_name))(obj)


def _to_tuple(x):
    return (x,) if not isinstance(x, Iterable) or isinstance(x, str) else tuple(x)


def _copy_func(func):
    """Based on https://stackoverflow.com/a/13503277/7523785."""
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
