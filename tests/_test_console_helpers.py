from __future__ import annotations

import functools


def empty_decorator(func):
    @functools.wraps(func)
    def wrapped():
        return func()

    return wrapped
