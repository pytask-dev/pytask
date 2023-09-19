from pytask import PythonNode
from pytask import task


nodes = [
    {"first": PythonNode(name="dict1"), "second": PythonNode(name="dict2")},
    (PythonNode(name="tuple1"), PythonNode(name="tuple2")),
    PythonNode(name="int"),
]


func = lambda *x: [{"first": "a", "second": {"b": 1, "c": 2}}, (3, 4), 5]


task_example = task(produces=nodes)(func)
