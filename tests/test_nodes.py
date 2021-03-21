from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import attr
import pytask
import pytest
from _pytask.nodes import _check_that_names_are_not_used_multiple_times
from _pytask.nodes import _convert_nodes_to_dictionary
from _pytask.nodes import _convert_objects_to_list_of_tuples
from _pytask.nodes import _convert_objects_to_node_dictionary
from _pytask.nodes import _create_task_name
from _pytask.nodes import _extract_nodes_from_function_markers
from _pytask.nodes import depends_on
from _pytask.nodes import FilePathNode
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.nodes import produces
from _pytask.nodes import PythonFunctionTask
from _pytask.nodes import reduce_node_name


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


@pytest.mark.unit
@pytest.mark.parametrize(
    ("x", "when", "expectation", "expected_lot", "expected_kd"),
    [
        (["string"], "depends_on", does_not_raise(), [("string",)], False),
        (("string",), "depends_on", does_not_raise(), [("string",)], False),
        (range(2), "depends_on", does_not_raise(), [(0,), (1,)], False),
        (
            [{"a": 0, "b": 1}],
            "depends_on",
            does_not_raise(),
            [("a", 0), ("b", 1)],
            False,
        ),
        (
            ["a", ("b", "c"), {"d": 1, "e": 1}],
            "depends_on",
            does_not_raise(),
            [("a",), ("b",), ("c",), ("d", 1), ("e", 1)],
            False,
        ),
        ([["string"]], "depends_on", does_not_raise(), [("string",)], True),
        ([{0: "string"}], "depends_on", does_not_raise(), [(0, "string")], True),
        (
            [((0, 1, 2),)],
            "depends_on",
            pytest.raises(ValueError, match="Dependencies in pytask.mark.depends_on"),
            None,
            None,
        ),
        (
            [((0, 1, 2),)],
            "produces",
            pytest.raises(ValueError, match="Products in pytask.mark.produces"),
            None,
            None,
        ),
    ],
)
def test_convert_objects_to_list_of_tuples(
    x, when, expectation, expected_lot, expected_kd
):
    with expectation:
        list_of_tuples, keep_dict = _convert_objects_to_list_of_tuples(x, when)
        assert list_of_tuples == expected_lot
        assert keep_dict is expected_kd


ERROR = "'@pytask.mark.depends_on' has nodes with the same name:"


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
@pytest.mark.parametrize(
    "path, name, expected",
    [
        (Path("hello.py"), "task_func", "hello.py::task_func"),
        (Path("C:/data/module.py"), "task_func", "C:/data/module.py::task_func"),
    ],
)
def test_create_task_name(path, name, expected):
    result = _create_task_name(path, name)
    assert result == expected


@attr.s
class DummyTask(MetaTask):
    path = attr.ib()
    name = attr.ib()
    base_name = attr.ib()

    def state():
        pass

    def execute():
        pass


@attr.s
class FalseNode:
    path = attr.ib()


_ROOT = Path.cwd()


@pytest.mark.integration
@pytest.mark.parametrize(
    "node, paths, expectation, expected",
    [
        (
            FilePathNode.from_path(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("alternative_src")],
            pytest.raises(ValueError, match="A node must be"),
            None,
        ),
        (
            FalseNode(_ROOT.joinpath("src/module.py")),
            [_ROOT.joinpath("src")],
            pytest.raises(ValueError, match="Unknown node"),
            None,
        ),
        (
            DummyTask(
                _ROOT.joinpath("top/src/module.py"),
                _ROOT.joinpath("top/src/module.py").as_posix() + "::task_func",
                "task_func",
            ),
            [_ROOT.joinpath("top/src")],
            does_not_raise(),
            "src/module.py::task_func",
        ),
        (
            FilePathNode.from_path(_ROOT.joinpath("top/src/module.py")),
            [_ROOT.joinpath("top/src")],
            does_not_raise(),
            "src/module.py",
        ),
        (
            PythonFunctionTask(
                "task_d",
                _ROOT.joinpath("top/src/module.py").as_posix() + "::task_d",
                _ROOT.joinpath("top/src/module.py"),
                lambda x: x,
            ),
            [_ROOT.joinpath("top/src/module.py")],
            does_not_raise(),
            "module.py::task_d",
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
    "objects, expectation, expected_dict, expected_kd",
    [
        ([0, 1], does_not_raise, {0: 0, 1: 1}, False),
        ([{0: 0}, {1: 1}], does_not_raise, {0: 0, 1: 1}, False),
        ([{0: 0}], does_not_raise, {0: 0}, True),
        ([[0]], does_not_raise, {0: 0}, True),
        ([((0, 0),), ((0, 1),)], ValueError, None, None),
        ([{0: 0}, {0: 1}], ValueError, None, None),
    ],
)
def test_convert_objects_to_node_dictionary(
    objects, when, expectation, expected_dict, expected_kd
):
    expectation = (
        pytest.raises(expectation, match=f"'@pytask.mark.{when}' has nodes")
        if expectation == ValueError
        else expectation()
    )
    with expectation:
        node_dict, keep_dict = _convert_objects_to_node_dictionary(objects, when)
        assert node_dict == expected_dict
        assert keep_dict is expected_kd
