"""Contains a cache."""

from __future__ import annotations

import functools
import hashlib
import inspect
from inspect import FullArgSpec
from typing import Any
from typing import Callable

from attrs import define
from attrs import field

from _pytask._hashlib import hash_value


@define
class CacheInfo:
    hits: int = 0
    misses: int = 0


@define
class Cache:
    _cache: dict[str, Any] = field(factory=dict)
    _sentinel: Any = field(factory=object)
    cache_info: CacheInfo = field(factory=CacheInfo)

    def memoize(self, func: Callable[..., Any]) -> Callable[..., Any]:
        prefix = f"{func.__module__}.{func.__name__}:"
        argspec = inspect.getfullargspec(func)

        @functools.wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Callable[..., Any]:
            key = _make_memoize_key(
                args, kwargs, typed=False, argspec=argspec, prefix=prefix
            )
            value = self._cache.get(key, self._sentinel)

            if value is self._sentinel:
                value = func(*args, **kwargs)
                self._cache[key] = value
                self.cache_info.misses += 1
            else:
                self.cache_info.hits += 1

            return value

        wrapped.cache = self  # type: ignore[attr-defined]

        return wrapped

    def add(self, key: str, value: Any) -> None:
        self._cache[key] = value


def _make_memoize_key(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    *,
    typed: bool,
    argspec: FullArgSpec,
    prefix: str,
) -> str:
    kwargs = kwargs.copy()
    key_args: tuple[Any, ...] = ()

    # Normalize args by moving positional arguments passed in as keyword arguments from
    # kwargs into args. This is so functions like foo(a, b, c) called with foo(1, b=2,
    # c=3) and foo(1, 2, 3) and foo(1, 2, c=3) will all have the same cache key.
    if kwargs:
        for i, arg in enumerate(argspec.args):
            if arg in kwargs:
                args = args[:i] + (kwargs.pop(arg),) + args[i:]

    if args:
        key_args += args

    if kwargs:
        # Separate args and kwargs with marker to avoid ambiguous cases where args
        # provided might look like some other args+kwargs combo.
        key_args += tuple(sorted(kwargs.items()))

    if typed and args:
        key_args += tuple(type(arg) for arg in args)

    if typed and kwargs:
        key_args += tuple(type(val) for _, val in sorted(kwargs.items()))

    # Hash everything in key_args and concatenate into a single byte string.
    raw_key = "".join(str(hash_value(key_arg)) for key_arg in key_args)

    # Combine prefix with md5 hash of raw key so that keys are normalized in length.
    return prefix + hashlib.md5(raw_key.encode()).hexdigest()  # noqa: S324
