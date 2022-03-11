from __future__ import annotations

import itertools
from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytask
import pytest
from _pytask.collect_utils import _check_that_names_are_not_used_multiple_times
from _pytask.collect_utils import _convert_objects_to_node_dictionary
from _pytask.collect_utils import _convert_to_dict
from _pytask.collect_utils import _extract_nodes_from_function_markers
from _pytask.collect_utils import _merge_dictionaries
from _pytask.collect_utils import _Placeholder
from pytask import depends_on
from pytask import produces


ERROR = "'@pytask.mark.depends_on' has nodes with the same name:"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("x", "expectation"),
    [
        ([{0: "a"}, {0: "b"}], pytest.raises(ValueError, match=ERROR)),
        ([{"a": 0}, {"a": 1}], pytest.raises(ValueError, match=ERROR)),
        ([{"a": 0}, {"b": 0}, {"a": 1}], pytest.raises(ValueError, match=ERROR)),
        ([{0: "a"}, {1: "a"}], does_not_raise()),
        ([{"a": 0}, {0: "a"}], does_not_raise()),
        ([{"a": 0}, {"b": 1}], does_not_raise()),
    ],
)
def test_check_that_names_are_not_used_multiple_times(x, expectation):
    with expectation:
        _check_that_names_are_not_used_multiple_times(x, "depends_on")


@pytest.mark.integration
@pytest.mark.parametrize("when", ["depends_on", "produces"])
@pytest.mark.parametrize(
    "objects, expectation, expected",
    [
        ([0, 1], does_not_raise, {0: 0, 1: 1}),
        ([{0: 0}, {1: 1}], does_not_raise, {0: 0, 1: 1}),
        ([{0: 0}], does_not_raise, {0: 0}),
        ([[0]], does_not_raise, {0: 0}),
        (
            [((0, 0),), ((0, 1),)],
            does_not_raise,
            {0: {0: 0, 1: 0}, 1: {0: 0, 1: 1}},
        ),
        ([{0: {0: {0: 0}}}, [2]], does_not_raise, {0: {0: {0: 0}}, 1: 2}),
        ([{0: 0}, {0: 1}], ValueError, None),
    ],
)
def test_convert_objects_to_node_dictionary(objects, when, expectation, expected):
    expectation = (
        pytest.raises(expectation, match=f"'@pytask.mark.{when}' has nodes")
        if expectation == ValueError
        else expectation()
    )
    with expectation:
        nodes = _convert_objects_to_node_dictionary(objects, when)
        assert nodes == expected


def _convert_placeholders_to_tuples(x):
    counter = itertools.count()
    return {
        (next(counter), k.scalar)
        if isinstance(k, _Placeholder)
        else k: _convert_placeholders_to_tuples(v)
        if isinstance(v, dict)
        else v
        for k, v in x.items()
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    "x, first_level, expected",
    [
        (1, True, {(0, True): 1}),
        ({1: 0}, False, {1: 0}),
        ({1: [2, 3]}, False, {1: {0: 2, 1: 3}}),
        ([2, 3], True, {(0, False): 2, (1, False): 3}),
        ([2, 3], False, {0: 2, 1: 3}),
    ],
)
def test__convert_to_dict(x, first_level, expected):
    """We convert placeholders to a tuple consisting of the key and the scalar bool."""
    result = _convert_to_dict(x, first_level)
    modified_result = _convert_placeholders_to_tuples(result)
    assert modified_result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "list_of_dicts, expected",
    [
        ([{1: 0}, {0: 1}], {1: 0, 0: 1}),
        ([{_Placeholder(): 1}, {0: 0}], {1: 1, 0: 0}),
        ([{_Placeholder(scalar=True): 1}], 1),
        ([{_Placeholder(scalar=False): 1}], {0: 1}),
    ],
)
def test_merge_dictionaries(list_of_dicts, expected):
    result = _merge_dictionaries(list_of_dicts)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "values, expected", [("a", ["a"]), (["b"], [["b"]]), (["e", "f"], [["e", "f"]])]
)
def test_extract_args_from_mark(decorator, values, expected):
    @decorator(values)
    def task_example():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(_extract_nodes_from_function_markers(task_example, parser))
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "values, expected",
    [
        ({"objects": "a"}, ["a"]),
        ({"objects": ["b"]}, [["b"]]),
        ({"objects": ["e", "f"]}, [["e", "f"]]),
    ],
)
def test_extract_kwargs_from_mark(decorator, values, expected):
    @decorator(**values)
    def task_example():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(_extract_nodes_from_function_markers(task_example, parser))
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "args, kwargs", [(["a", "b"], {"objects": "a"}), (("a"), {"objects": "a"})]
)
def test_raise_error_for_invalid_args_to_depends_on_and_produces(
    decorator, args, kwargs
):
    @decorator(*args, **kwargs)
    def task_example():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    with pytest.raises(TypeError):
        list(_extract_nodes_from_function_markers(task_example, parser))
