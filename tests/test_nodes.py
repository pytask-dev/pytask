from contextlib import ExitStack as does_not_raise  # noqa: N813
from pathlib import Path

import attr
import pytask
import pytest
from _pytask.nodes import _check_that_names_are_not_used_multiple_times
from _pytask.nodes import _convert_nodes_to_dictionary
from _pytask.nodes import _convert_objects_to_list_of_tuples
from _pytask.nodes import _create_task_name
from _pytask.nodes import _extract_nodes_from_function_markers
from _pytask.nodes import _find_closest_ancestor
from _pytask.nodes import _relative_to
from _pytask.nodes import depends_on
from _pytask.nodes import FilePathNode
from _pytask.nodes import MetaNode
from _pytask.nodes import MetaTask
from _pytask.nodes import produces
from _pytask.nodes import shorten_node_name


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


@pytest.mark.unit
@pytest.mark.parametrize(
    "path, source, include_source, expected",
    [
        (Path("src/hello.py"), Path("src"), True, Path("src/hello.py")),
        (Path("src/hello.py"), Path("src"), False, Path("hello.py")),
    ],
)
def test_relative_to(path, source, include_source, expected):
    result = _relative_to(path, source, include_source)
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "path, potential_ancestors, expected",
    [
        (Path("src/task.py"), [Path("src"), Path("bld")], Path("src")),
        (Path("tasks/task.py"), [Path("src"), Path("bld")], None),
        (Path("src/tasks/task.py"), [Path("src"), Path("src/tasks")], Path("tasks")),
    ],
)
def task_find_closest_ancestor(path, potential_ancestors, expected):
    result = _find_closest_ancestor(path, potential_ancestors)
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


@pytest.mark.integration
@pytest.mark.parametrize(
    "node, paths, expectation, expected",
    [
        (
            FilePathNode.from_path(Path("src/module.py")),
            [Path("src")],
            pytest.raises(ValueError, match="A node must be"),
            None,
        ),
        (
            FalseNode(Path("src/module.py")),
            [Path("src")],
            pytest.raises(ValueError, match="Unknown node"),
            None,
        ),
        (
            DummyTask(
                Path("top/src/module.py"), "top/src/module.py::task_func", "task_func"
            ),
            [Path("top/src")],
            does_not_raise(),
            "src/module.py::task_func",
        ),
        (
            FilePathNode.from_path(Path("top/src/module.py").resolve()),
            [Path("top/src").resolve()],
            does_not_raise(),
            "src/module.py",
        ),
    ],
)
def test_shorten_node_name(node, paths, expectation, expected):
    with expectation:
        result = shorten_node_name(node, paths)
        assert result == expected
