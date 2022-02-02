from __future__ import annotations

import itertools
from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import attr
import pytask
import pytest
from _pytask.nodes import _check_that_names_are_not_used_multiple_times
from _pytask.nodes import _convert_objects_to_node_dictionary
from _pytask.nodes import _extract_nodes_from_function_markers
from _pytask.nodes import _Placeholder
from _pytask.nodes import convert_to_dict
from _pytask.nodes import create_task_name
from _pytask.nodes import depends_on
from _pytask.nodes import FilePathNode
from _pytask.nodes import merge_dictionaries
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.nodes import produces
from _pytask.shared import reduce_node_name


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


@pytest.mark.unit
def test_instantiation_of_metatask():
    class Task(MetaTask):
        pass

    with pytest.raises(TypeError):
        Task()

    class Task(MetaTask):
        def execute(self):
            ...

        def state(self):
            ...

        def add_report_section(self):
            ...

    task = Task()
    assert isinstance(task, MetaTask)


@pytest.mark.unit
def test_instantiation_of_metanode():
    class Node(MetaNode):
        ...

    with pytest.raises(TypeError):
        Node()

    class Node(MetaNode):
        def state(self):
            ...

    task = Node()
    assert isinstance(task, MetaNode)


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


@pytest.mark.unit
@pytest.mark.parametrize(
    "path, name, expected",
    [
        (Path("hello.py"), "task_func", "hello.py::task_func"),
        (Path("C:/data/module.py"), "task_func", "C:/data/module.py::task_func"),
    ],
)
def test_create_task_name(path, name, expected):
    result = create_task_name(path, name)
    assert result == expected


@attr.s
class FalseNode:
    path = attr.ib()


_ROOT = Path.cwd()


@pytest.mark.integration
@pytest.mark.parametrize(
    "node, paths, expectation, expected",
    [
        pytest.param(
            FilePathNode.from_path(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("alternative_src")],
            does_not_raise(),
            "pytask/src/module.py",
            id="Common path found for FilePathNode not in 'paths' and 'paths'",
        ),
        pytest.param(
            FalseNode(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("src")],
            pytest.raises(TypeError, match="Unknown node"),
            None,
            id="throw error on unknown node type.",
        ),
        pytest.param(
            FilePathNode.from_path(_ROOT.joinpath("top/src/module.py")),
            [_ROOT.joinpath("top/src")],
            does_not_raise(),
            "src/module.py",
            id="make filepathnode relative to 'paths'.",
        ),
    ],
)
def test_reduce_node_name(node, paths, expectation, expected):
    with expectation:
        result = reduce_node_name(node, paths)
        assert result == expected


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
def test_convert_to_dict(x, first_level, expected):
    """We convert placeholders to a tuple consisting of the key and the scalar bool."""
    result = convert_to_dict(x, first_level)
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
    result = merge_dictionaries(list_of_dicts)
    assert result == expected
