from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from pytask import is_task_function

if TYPE_CHECKING:
    from typing_extensions import assert_type

    from pytask import CollectionMetadata
    from pytask import task

    @task
    def _typed_task(value: int) -> str:
        return str(value)

    assert_type(_typed_task(1), str)
    assert_type(_typed_task.pytask_meta, CollectionMetadata)


def test_is_task_function():
    def func(): ...

    assert is_task_function(func)

    partialed_func = functools.partial(func)
    assert is_task_function(partialed_func)

    assert is_task_function(lambda x: x)

    partialed_lambda = functools.partial(lambda x: x)
    assert is_task_function(partialed_lambda)
