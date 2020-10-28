from contextlib import ExitStack as does_not_raise  # noqa: N813

import pytask
import pytest
from _pytask.nodes import _check_that_names_are_not_used_multiple_times
from _pytask.nodes import _convert_nodes_to_dictionary
from _pytask.nodes import _convert_objects_to_list_of_tuples
from _pytask.nodes import _extract_nodes_from_function_markers
from _pytask.nodes import depends_on
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.nodes import produces


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "values, expected", [("a", ["a"]), (["b"], [["b"]]), (["e", "f"], [["e", "f"]])]
)
def test_extract_args_from_mark(decorator, values, expected):
    @decorator(values)
    def task_dummy():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(_extract_nodes_from_function_markers(task_dummy, parser))
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
    def task_dummy():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(_extract_nodes_from_function_markers(task_dummy, parser))
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
    def task_dummy():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    with pytest.raises(TypeError):
        list(_extract_nodes_from_function_markers(task_dummy, parser))


@pytest.mark.unit
def test_instantiation_of_metatask():
    class Task(MetaTask):
        pass

    with pytest.raises(TypeError):
        Task()

    class Task(MetaTask):
        def execute(self):
            pass

        def state(self):
            pass

    task = Task()
    assert isinstance(task, MetaTask)


@pytest.mark.unit
def test_instantiation_of_metanode():
    class Node(MetaNode):
        pass

    with pytest.raises(TypeError):
        Node()

    class Node(MetaNode):
        def state(self):
            pass

    task = Node()
    assert isinstance(task, MetaNode)


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (["string"], [("string",)]),
        (("string",), [("string",)]),
        (range(2), [(0,), (1,)]),
        ([{"a": 0, "b": 1}], [("a", 0), ("b", 1)]),
        (
            ["a", ("b", "c"), {"d": 1, "e": 1}],
            [("a",), ("b",), ("c",), ("d", 1), ("e", 1)],
        ),
    ],
)
def test_convert_objects_to_list_of_tuples(x, expected):
    result = _convert_objects_to_list_of_tuples(x)
    assert result == expected


ERROR = "'@pytask.mark.depends_on' has nodes with the same name:"


@pytest.mark.parametrize(
    ("x", "expectation"),
    [
        ([(0, "a"), (0, "b")], pytest.raises(ValueError, match=ERROR)),
        ([("a", 0), ("a", 1)], pytest.raises(ValueError, match=ERROR)),
        ([("a", 0), ("b",), ("a", 1)], pytest.raises(ValueError, match=ERROR)),
        ([("a", 0), ("b", 0), ("a", 1)], pytest.raises(ValueError, match=ERROR)),
        ([("a",), ("a")], does_not_raise()),
        ([("a", 0), ("a",)], does_not_raise()),
        ([("a", 0), ("b", 1)], does_not_raise()),
    ],
)
def test_check_that_names_are_not_used_multiple_times(x, expectation):
    with expectation:
        _check_that_names_are_not_used_multiple_times(x, "depends_on")


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        ([("a",), ("b",)], {0: "a", 1: "b"}),
        ([(1, "a"), ("b",), (0, "c")], {1: "a", 2: "b", 0: "c"}),
    ],
)
def test_convert_nodes_to_dictionary(x, expected):
    result = _convert_nodes_to_dictionary(x)
    assert result == expected
