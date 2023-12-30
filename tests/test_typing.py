from __future__ import annotations

import functools

import pytest
from pytask import is_task_function


@pytest.mark.unit()
def test_is_task_function():
    def func():
        ...

    assert is_task_function(func)

    partialed_func = functools.partial(func)
    assert is_task_function(partialed_func)

    assert is_task_function(lambda x: x)

    partialed_lambda = functools.partial(lambda x: x)
    assert is_task_function(partialed_lambda)
