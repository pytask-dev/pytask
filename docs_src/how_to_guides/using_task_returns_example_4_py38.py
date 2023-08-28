from typing import Any

from pytask import PythonNode
from typing_extensions import Annotated


nodes = [
    {"first": PythonNode(name="dict1"), "second": PythonNode(name="dict2")},
    (PythonNode(name="tuple1"), PythonNode(name="tuple2")),
    PythonNode(name="int"),
]


def task_example() -> Annotated[Any, nodes]:
    return [{"first": "a", "second": {"b": 1, "c": 2}}, (3, 4), 5]
