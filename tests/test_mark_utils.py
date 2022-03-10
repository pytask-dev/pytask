from __future__ import annotations

from pathlib import Path

import pytask
import pytest
from _pytask.models import CollectionMetadata
from pytask import get_marks
from pytask import has_mark
from pytask import remove_marks
from pytask import Task


@pytest.mark.unit
@pytest.mark.parametrize(
    "markers, marker_name, expected",
    [
        ([], "not_found", []),
        (
            [pytask.mark.produces(), pytask.mark.depends_on()],
            "produces",
            [pytask.mark.produces()],
        ),
        (
            [pytask.mark.produces(), pytask.mark.produces(), pytask.mark.depends_on()],
            "produces",
            [pytask.mark.produces(), pytask.mark.produces()],
        ),
    ],
)
def test_get_specific_markers_from_task(markers, marker_name, expected):
    task = Task(base_name="name", path=Path(), function=None, markers=markers)
    result = get_marks(task, marker_name)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "markers, marker_name, expected",
    [
        (None, "not_found", []),
        ([], "not_found", []),
        (
            [pytask.mark.produces(), pytask.mark.depends_on()],
            "produces",
            [pytask.mark.produces()],
        ),
        (
            [pytask.mark.produces(), pytask.mark.produces(), pytask.mark.depends_on()],
            "produces",
            [pytask.mark.produces(), pytask.mark.produces()],
        ),
    ],
)
def test_get_marks_from_obj(markers, marker_name, expected):
    def func():
        ...

    if markers is not None:
        func.pytask_meta = CollectionMetadata(markers=markers)

    result = get_marks(func, marker_name)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "markers, marker_name, expected",
    [
        (None, "not_found", False),
        ([], "not_found", False),
        ([pytask.mark.produces(), pytask.mark.depends_on()], "produces", True),
        (
            [pytask.mark.produces(), pytask.mark.produces(), pytask.mark.depends_on()],
            "produces",
            True,
        ),
    ],
)
def test_has_marker(markers, marker_name, expected):
    def func():
        ...

    if markers is not None:
        func.pytask_meta = CollectionMetadata(markers=markers)

    result = has_mark(func, marker_name)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "markers, marker_name, expected_markers, expected_others",
    [
        (None, "not_found", [], []),
        ([], "not_found", [], []),
        (
            [pytask.mark.produces(), pytask.mark.depends_on()],
            "produces",
            [pytask.mark.produces()],
            [pytask.mark.depends_on()],
        ),
        (
            [pytask.mark.produces(), pytask.mark.produces(), pytask.mark.depends_on()],
            "produces",
            [pytask.mark.produces(), pytask.mark.produces()],
            [pytask.mark.depends_on()],
        ),
    ],
)
def test_remove_markers_from_func(
    markers, marker_name, expected_markers, expected_others
):
    def func():
        ...

    if markers is not None:
        func.pytask_meta = CollectionMetadata(markers=markers)

    obj, result_markers = remove_marks(func, marker_name)
    markers = obj.pytask_meta.markers if hasattr(obj, "pytask_meta") else []
    assert markers == expected_others
    assert result_markers == expected_markers
