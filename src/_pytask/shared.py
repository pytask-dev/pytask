from collections.abc import Iterable


def to_list(scalar_or_iter):
    """Convert scalars and iterables to list.

    Parameters
    ----------
    scalar_or_iter : str or list

    Returns
    -------
    list

    Examples
    --------
    >>> to_list("a")
    ['a']
    >>> to_list(["b"])
    ['b']

    """
    return (
        [scalar_or_iter]
        if isinstance(scalar_or_iter, str) or not isinstance(scalar_or_iter, Iterable)
        else list(scalar_or_iter)
    )


def get_first_not_none_value(*configs, key, default=None, callback=None):
    """Get the first non-None value for a key from a list of dictionaries.

    This function allows to prioritize information from many configurations by changing
    the order of the inputs while also providing a default.

    Examples
    --------
    >>> get_first_not_none_value({"a": None}, {"a": 1}, key="a")
    1

    >>> get_first_not_none_value({"a": None}, {"a": None}, key="a", default="default")
    'default'

    >>> get_first_not_none_value({}, {}, key="a", default="default")
    'default'

    >>> get_first_not_none_value({"a": None}, {"a": "b"}, key="a", callback=to_list)
    ['b']

    """
    return next(
        (
            config[key] if callback is None else callback(config[key])
            for config in configs
            if config.get(key) is not None
        ),
        default,
    )


def remove_traceback_from_exc_info(exc_info):
    """Remove traceback from exception."""
    return (*exc_info[:2], None)
