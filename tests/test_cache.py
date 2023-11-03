from __future__ import annotations

import inspect

from _pytask.cache import _make_memoize_key
from _pytask.cache import Cache


def test_cache():
    cache = Cache()

    @cache.memoize
    def func(a):
        return a

    assert func.cache.cache_info.hits == 0
    assert func.cache.cache_info.misses == 0

    value = func(1)
    assert value == 1
    assert func.cache.cache_info.hits == 0
    assert func.cache.cache_info.misses == 1

    assert next(i for i in cache._cache.values()) == 1

    value = func(1)
    assert value == 1
    assert func.cache.cache_info.hits == 1
    assert func.cache.cache_info.misses == 1


def test_cache_add():
    cache = Cache()

    @cache.memoize
    def func(a):
        return a

    prefix = f"{func.__module__}.{func.__name__}:"
    argspec = inspect.getfullargspec(func)
    key = _make_memoize_key((1,), {}, typed=False, argspec=argspec, prefix=prefix)
    cache.add(key, 1)

    value = func(1)
    assert value == 1
    assert cache.cache_info.hits == 1
    assert cache.cache_info.misses == 0

    value = func(2)
    assert value == 2
    assert cache.cache_info.hits == 1
    assert cache.cache_info.misses == 1
