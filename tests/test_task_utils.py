from __future__ import annotations

from contextlib import ExitStack as does_not_raise  # noqa: N813
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import NamedTuple

import pytest

from _pytask.task_utils import COLLECTED_TASKS
from _pytask.task_utils import _arg_value_to_id_component
from _pytask.task_utils import _parse_name
from _pytask.task_utils import _parse_task_kwargs
from pytask import Mark
from pytask import task


@pytest.mark.parametrize(
    ("arg_name", "arg_value", "i", "id_func", "expected"),
    [
        ("arg", 1, 0, None, "1"),
        ("arg", True, 0, None, "True"),
        ("arg", False, 0, None, "False"),
        ("arg", 1.0, 0, None, "1.0"),
        ("arg", None, 0, None, "arg0"),
        ("arg", (1,), 0, None, "arg0"),
        ("arg", [1], 0, None, "arg0"),
        ("arg", {1, 2}, 0, None, "arg0"),
        ("arg", 1, 0, bool, "True"),
        ("arg", 1, 1, lambda x: None, "1"),  # noqa: ARG005
        ("arg", [1], 2, lambda x: None, "arg2"),  # noqa: ARG005
    ],
)
def test_arg_value_to_id_component(arg_name, arg_value, i, id_func, expected):
    result = _arg_value_to_id_component(arg_name, arg_value, i, id_func)
    assert result == expected


class ExampleNT(NamedTuple):
    a: int = 1


@dataclass
class ExampleDataclass:
    b: str = "wonderful"


@pytest.mark.parametrize(
    ("kwargs", "expectation", "expected"),
    [
        ({"hello": 1}, does_not_raise(), {"hello": 1}),
        (ExampleNT(), does_not_raise(), {"a": 1}),
        (ExampleNT, pytest.raises(TypeError, match=r"(_asdict\(\) missing 1)"), None),
        (ExampleDataclass(), does_not_raise(), {"b": "wonderful"}),
        (ExampleDataclass, pytest.raises(ValueError, match="@task"), None),
        (1, pytest.raises(ValueError, match="@task"), None),
    ],
)
def test_parse_task_kwargs(kwargs, expectation, expected):
    with expectation:
        result = _parse_task_kwargs(kwargs)
        assert result == expected


def test_default_values_of_pytask_meta():
    @task()
    def task_example(): ...

    assert task_example.pytask_meta.after == []
    assert not task_example.pytask_meta.is_generator
    assert task_example.pytask_meta.id_ is None
    assert task_example.pytask_meta.kwargs == {}
    assert task_example.pytask_meta.markers == [Mark("task", (), {})]
    assert task_example.pytask_meta.name == "task_example"
    assert task_example.pytask_meta.produces is None

    # Remove collected task.
    COLLECTED_TASKS.pop(Path(__file__))


def task_func(x):  # pragma: no cover
    pass


@pytest.mark.parametrize(
    ("func", "name", "expectation", "expected"),
    [
        (task_func, None, does_not_raise(), "task_func"),
        (task_func, "name", does_not_raise(), "name"),
        (partial(task_func, x=1), None, does_not_raise(), "task_func"),
        (partial(task_func, x=1), "name", does_not_raise(), "name"),
        (lambda x: None, None, does_not_raise(), "<lambda>"),  # noqa: ARG005
        (partial(lambda x: None, x=1), None, does_not_raise(), "<lambda>"),  # noqa: ARG005
        (1, None, pytest.raises(NotImplementedError, match="Cannot"), None),
    ],
)
def test_parse_name(func, name, expectation, expected):
    with expectation:
        result = _parse_name(func, name)
        assert result == expected
