import attr
import pytask
import pytest
from _pytask.mark_utils import get_marks_from_obj
from _pytask.mark_utils import get_specific_markers_from_task
from _pytask.mark_utils import has_marker
from _pytask.mark_utils import remove_markers_from_func
from _pytask.nodes import MetaTask


@attr.s
class Task(MetaTask):
    markers = attr.ib(factory=list)

    def execute(self):
        ...

    def state(self):
        ...

    def add_report_section(self):
        ...


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
    task = Task()
    task.markers = markers
    result = get_specific_markers_from_task(task, marker_name)
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
        func.pytaskmark = markers

    result = get_marks_from_obj(func, marker_name)
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
        func.pytaskmark = markers

    result = has_marker(func, marker_name)
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
        func.pytaskmark = markers

    obj, result_markers = remove_markers_from_func(func, marker_name)
    assert obj.pytaskmark == expected_others
    assert result_markers == expected_markers
