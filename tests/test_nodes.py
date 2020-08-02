import pytask
import pytest
from pytask.nodes import depends_on
from pytask.nodes import extract_nodes_from_function_markers
from pytask.nodes import MetaNode
from pytask.nodes import MetaTask
from pytask.nodes import produces


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "values, expected", [("a", ["a"]), (["b"], ["b"]), (["e", "f"], ["e", "f"])]
)
def test_extract_args_from_mark(decorator, values, expected):
    @decorator(values)
    def task_dummy():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(extract_nodes_from_function_markers(task_dummy, parser))
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize("decorator", [pytask.mark.depends_on, pytask.mark.produces])
@pytest.mark.parametrize(
    "values, expected",
    [
        ({"objects": "a"}, ["a"]),
        ({"objects": ["b"]}, ["b"]),
        ({"objects": ["e", "f"]}, ["e", "f"]),
    ],
)
def test_extract_kwargs_from_mark(decorator, values, expected):
    @decorator(**values)
    def task_dummy():
        pass

    parser = depends_on if decorator.name == "depends_on" else produces
    result = list(extract_nodes_from_function_markers(task_dummy, parser))
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
        list(extract_nodes_from_function_markers(task_dummy, parser))


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
