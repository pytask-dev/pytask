from __future__ import annotations

import inspect

import pytest
from _pytask.cache import Cache
from _pytask.cache import _make_memoize_key


@pytest.mark.unit()
def test_cache():
    cache = Cache()

    @cache.memoize
    def func(a, b):
        return a + b

    assert func.cache.cache_info.hits == 0
    assert func.cache.cache_info.misses == 0

    value = func(1, b=2)
    assert value == 3
    assert func.cache.cache_info.hits == 0
    assert func.cache.cache_info.misses == 1

    assert next(i for i in cache._cache.values()) == 3

    value = func(1, b=2)
    assert value == 3
    assert func.cache.cache_info.hits == 1
    assert func.cache.cache_info.misses == 1


@pytest.mark.unit()
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


@pytest.mark.unit()
def test_make_memoize_key():
    def func(a, b):  # pragma: no cover
        return a + b

    argspec = inspect.getfullargspec(func)
    # typed makes the key different each run.
    key = _make_memoize_key(
        (1,), {"b": 2}, typed=True, argspec=argspec, prefix="prefix"
    )
    assert key.startswith("prefix")
