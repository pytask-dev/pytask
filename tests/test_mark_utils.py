from __future__ import annotations

from pathlib import Path

import pytest

import pytask
from pytask import CollectionMetadata
from pytask import Task
from pytask import get_all_marks
from pytask import get_marks
from pytask import has_mark
from pytask import remove_marks
from pytask import set_marks


@pytest.mark.parametrize(
    ("markers", "expected"),
    [
        ([], []),
        (
            [pytask.mark.mark1(), pytask.mark.mark2()],
            [pytask.mark.mark1(), pytask.mark.mark2()],
        ),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
        ),
    ],
)
def test_get_all_marks_from_task(markers, expected):
    task = Task(base_name="name", path=Path(), function=None, markers=markers)  # type: ignore[arg-type]
    result = get_all_marks(task)
    assert result == expected


@pytest.mark.parametrize(
    ("markers", "expected"),
    [
        (None, []),
        ([], []),
        (
            [pytask.mark.mark1(), pytask.mark.mark2()],
            [pytask.mark.mark1(), pytask.mark.mark2()],
        ),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
        ),
    ],
)
def test_get_all_marks_from_obj(markers, expected):
    def func(): ...

    if markers is not None:
        func.pytask_meta = CollectionMetadata(markers=markers)  # type: ignore[attr-defined]

    result = get_all_marks(func)
    assert result == expected


@pytest.mark.parametrize(
    ("markers", "marker_name", "expected"),
    [
        ([], "not_found", []),
        (
            [pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1()],
        ),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1(), pytask.mark.mark1()],
        ),
    ],
)
def test_get_marks_from_task(markers, marker_name, expected):
    task = Task(base_name="name", path=Path(), function=None, markers=markers)  # type: ignore[arg-type]
    result = get_marks(task, marker_name)
    assert result == expected


@pytest.mark.parametrize(
    ("markers", "marker_name", "expected"),
    [
        (None, "not_found", []),
        ([], "not_found", []),
        (
            [pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1()],
        ),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1(), pytask.mark.mark1()],
        ),
    ],
)
def test_get_marks_from_obj(markers, marker_name, expected):
    def func(): ...

    if markers is not None:
        func.pytask_meta = CollectionMetadata(markers=markers)  # type: ignore[attr-defined]

    result = get_marks(func, marker_name)
    assert result == expected


@pytest.mark.parametrize(
    ("markers", "marker_name", "expected"),
    [
        ([pytask.mark.mark1()], "not_found", False),
        (
            [pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            True,
        ),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            "other",
            False,
        ),
    ],
)
def test_has_mark_for_task(markers, marker_name, expected):
    task = Task(base_name="name", path=Path(), function=None, markers=markers)  # type: ignore[arg-type]
    result = has_mark(task, marker_name)
    assert result is expected


@pytest.mark.parametrize(
    ("markers", "marker_name", "expected"),
    [
        (None, "not_found", False),
        ([], "not_found", False),
        ([pytask.mark.mark1(), pytask.mark.mark2()], "mark1", True),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            True,
        ),
    ],
)
def test_has_mark(markers, marker_name, expected):
    def func(): ...

    if markers is not None:
        func.pytask_meta = CollectionMetadata(markers=markers)  # type: ignore[attr-defined]

    result = has_mark(func, marker_name)
    assert result == expected


@pytest.mark.parametrize(
    ("markers", "marker_name", "expected_markers", "expected_others"),
    [
        ([], "not_found", [], []),
        (
            [pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1()],
            [pytask.mark.mark2()],
        ),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1(), pytask.mark.mark1()],
            [pytask.mark.mark2()],
        ),
    ],
)
def test_remove_marks_from_task(
    markers, marker_name, expected_markers, expected_others
):
    task = Task(base_name="name", path=Path(), function=None, markers=markers)  # type: ignore[arg-type]
    _, result_markers = remove_marks(task, marker_name)
    assert task.markers == expected_others
    assert result_markers == expected_markers


@pytest.mark.parametrize(
    ("markers", "marker_name", "expected_markers", "expected_others"),
    [
        (None, "not_found", [], []),
        ([], "not_found", [], []),
        (
            [pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1()],
            [pytask.mark.mark2()],
        ),
        (
            [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
            "mark1",
            [pytask.mark.mark1(), pytask.mark.mark1()],
            [pytask.mark.mark2()],
        ),
    ],
)
def test_remove_marks_from_func(
    markers, marker_name, expected_markers, expected_others
):
    def func(): ...

    if markers is not None:
        func.pytask_meta = CollectionMetadata(markers=markers)  # type: ignore[attr-defined]

    obj, result_markers = remove_marks(func, marker_name)
    markers = get_all_marks(obj)
    assert markers == expected_others
    assert result_markers == expected_markers


@pytest.mark.parametrize(
    "markers",
    [
        [],
        [pytask.mark.mark1(), pytask.mark.mark2()],
        [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
    ],
)
def test_set_marks_to_task(markers):
    task = Task(base_name="name", path=Path(), function=None)  # type: ignore[arg-type]
    result = set_marks(task, markers)
    assert result.markers == markers


@pytest.mark.parametrize(
    "markers",
    [
        [],
        [pytask.mark.mark1(), pytask.mark.mark2()],
        [pytask.mark.mark1(), pytask.mark.mark1(), pytask.mark.mark2()],
    ],
)
def test_set_marks_to_obj(markers):
    def func(): ...

    result = set_marks(func, markers)
    assert result.pytask_meta.markers == markers  # type: ignore[union-attr]
