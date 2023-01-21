from __future__ import annotations

from typing import Any
from typing import Callable


def arg_value_to_id_component(
    arg_name: str, arg_value: Any, i: int, id_func: Callable[..., Any] | None
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
    id_func : Union[Callable[..., Any], None]
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
