from __future__ import annotations

import functools


def empty_decorator(func):
    @functools.wraps(func)
    def wrapped():  # pragma: no cover
        return func()

    return wrapped
