import pytask
import pytest
from pytask.nodes import extract_nodes_from_mark
from pytask.nodes import MetaNode
from pytask.nodes import MetaTask


@pytest.mark.unit
def test_extract_dependencies_from_mark():
    @pytask.mark.depends_on("a")
    @pytask.mark.depends_on(["b"])
    @pytask.mark.depends_on("c", "d")
    @pytask.mark.depends_on(["e", "f"])
    def dummy_function():
        pass

    result = list(extract_nodes_from_mark(dummy_function, "depends_on"))

    assert list("abcdef") == sorted(result)


@pytest.mark.unit
def test_extract_products_from_mark():
    @pytask.mark.produces("a")
    @pytask.mark.produces(["b"])
    @pytask.mark.produces("c", "d")
    @pytask.mark.produces(["e", "f"])
    def dummy_function():
        pass

    result = list(extract_nodes_from_mark(dummy_function, "produces"))

    assert list("abcdef") == sorted(result)


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
