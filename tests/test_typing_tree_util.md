# tree_leaves

Flattening a tree should preserve the type of its node leaves.

Checker-specific error comments record current diagnostics for valid node use cases.
The desired revealed types remain assertions, so inference mismatches still fail.

## Concrete nodes in different containers

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)

```python
from pathlib import Path
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_leaves

path_node = PathNode(path=Path("input.txt"))
python_node = PythonNode(value="input")

reveal_type(tree_leaves(path_node))  # revealed: list[PathNode]
reveal_type(tree_leaves([path_node]))  # revealed: list[PathNode]
reveal_type(tree_leaves((path_node,)))  # revealed: list[PathNode]
reveal_type(tree_leaves({"input": path_node}))  # revealed: list[PathNode]

reveal_type(tree_leaves(python_node))  # revealed: list[PythonNode]
reveal_type(tree_leaves([python_node]))  # revealed: list[PythonNode]
reveal_type(tree_leaves((python_node,)))  # revealed: list[PythonNode]
reveal_type(tree_leaves({"input": python_node}))  # revealed: list[PythonNode]
```

## Flat containers of concrete and provisional node protocols

```python
from typing_extensions import reveal_type

from pytask import PNode, PProvisionalNode
from pytask.tree_util import tree_leaves


def check_flat_nodes(
    node: PProvisionalNode,
    nodes: list[PNode | PProvisionalNode],
    tuple_nodes: tuple[PNode | PProvisionalNode, ...],
    named_nodes: dict[str, PNode | PProvisionalNode],
) -> None:
    reveal_type(tree_leaves(node))  # revealed: list[PProvisionalNode]
    reveal_type(tree_leaves(nodes))  # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(tuple_nodes))  # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(named_nodes))  # revealed: list[PNode | PProvisionalNode]
```

## Custom leaf predicates retain the general traversal contract

A predicate can treat the entire list as one leaf. Node-container overloads must
not promise individual nodes in that case.

```python
from typing_extensions import reveal_type

from pytask import PythonNode
from pytask.tree_util import tree_leaves

nodes = [PythonNode(value="input")]
reveal_type(tree_leaves(nodes, is_leaf=None))  # revealed: list[PythonNode]
# revealed: list[list[PythonNode]]
reveal_type(tree_leaves(nodes, is_leaf=lambda value: isinstance(value, list)))
```

## Nested containers of concrete nodes

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [Pyright #9798](https://github.com/microsoft/pyright/issues/9798)

```python
from pathlib import Path
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_leaves

paths: dict[str, list[tuple[PathNode, ...]]] = {
    "inputs": [(PathNode(path=Path("input.txt")),)],
}
objects: list[dict[str, tuple[PythonNode, ...]]] = [
    {"inputs": (PythonNode(value="input"),)},
]

reveal_type(tree_leaves(paths))  # revealed: list[PathNode]
reveal_type(tree_leaves(objects))  # revealed: list[PythonNode]
```

## Mixed concrete node types

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [mypy #6751](https://github.com/python/mypy/issues/6751)

```python
from pathlib import Path
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_leaves

nodes: list[PathNode | PythonNode] = [
    PathNode(path=Path("input.txt")),
    PythonNode(value="input"),
]

reveal_type(tree_leaves(nodes))  # revealed: list[PathNode | PythonNode]
```

## Trees annotated with the node protocol

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)

```python
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_leaves


def check_node_tree(tree: PyTree[PNode]) -> None:
    leaves = tree_leaves(tree)
    reveal_type(leaves)  # revealed: list[PNode]
    for node in leaves:
        # ty-error: [unresolved-attribute]
        reveal_type(node.signature)  # revealed: str
        # ty-error: [unresolved-attribute]
        reveal_type(node.state())  # revealed: str | None
        # ty-error: [unresolved-attribute]
        node.load()
```

## Task dependencies and products include provisional nodes

Plugins receive `PTask`, whose argument dictionaries contain concrete or provisional
nodes. This is a broader contract than `PyTree[PNode]`.

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [mypy #6751](https://github.com/python/mypy/issues/6751)
- [mypy #22063](https://github.com/python/mypy/issues/22063)

```python
from typing_extensions import reveal_type

from pytask import PTask
from pytask.tree_util import tree_leaves


def check_task_nodes(task: PTask) -> None:
    # mypy-error: [type-var]
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(task.depends_on))
    # mypy-error: [type-var]
    reveal_type(tree_leaves(task.produces))  # revealed: list[PNode | PProvisionalNode]
```

## Discover paths in task nodes

Based on `pytask-latex`'s dependency and product discovery. Narrowing a flattened leaf
to `PPathNode` must allow access to its path without casts or ignores.

Related issues:

- [mypy #6751](https://github.com/python/mypy/issues/6751)
- [mypy #22063](https://github.com/python/mypy/issues/22063)

```python
from typing_extensions import reveal_type

from pytask import PPathNode, PTask
from pytask.tree_util import tree_leaves


def check_task_paths(task: PTask) -> set[str]:
    paths: set[str] = set()
    # mypy-error: [type-var]
    for node in tree_leaves(task.depends_on):
        if isinstance(node, PPathNode):
            reveal_type(node.path.as_posix())  # revealed: str
            paths.add(node.path.as_posix())
    # mypy-error: [type-var]
    for node in tree_leaves(task.produces):
        if isinstance(node, PPathNode):
            paths.add(node.path.as_posix())
    return paths
```
