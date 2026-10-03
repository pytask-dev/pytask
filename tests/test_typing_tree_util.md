# tree_leaves

Flattening a tree should preserve the type of its node leaves.

Checker-specific error comments record current diagnostics for valid node use cases.
Intended types are documented beside the assertions of each checker's current output.
These snapshots use ty 0.0.84, Pyright 1.1.414, Pyrefly 1.3.2, and mypy 2.4.0.
Changes to the revealed output fail the tests and should be reviewed against the
intended types. Mypy's qualified node names are preserved exactly.

## Concrete nodes in different containers

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)

Intended types:

- `reveal_type(tree_leaves(path_node))`: `list[PathNode]`.
- `reveal_type(tree_leaves([path_node]))`: `list[PathNode]`.
- `reveal_type(tree_leaves((path_node,)))`: `list[PathNode]`.
- `reveal_type(tree_leaves({"input": path_node}))`: `list[PathNode]`.
- `reveal_type(tree_leaves(python_node))`: `list[PythonNode]`.
- `reveal_type(tree_leaves([python_node]))`: `list[PythonNode]`.
- `reveal_type(tree_leaves((python_node,)))`: `list[PythonNode]`.
- `reveal_type(tree_leaves({"input": python_node}))`: `list[PythonNode]`.

Current reveals (ty, pyright, pyrefly):

```python only=ty,pyright,pyrefly
from pathlib import Path
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_leaves

path_node = PathNode(path=Path("input.txt"))
python_node = PythonNode(value="input")

# revealed: list[PathNode]
reveal_type(tree_leaves(path_node))
# revealed: list[PathNode]
reveal_type(tree_leaves([path_node]))
# revealed: list[PathNode]
reveal_type(tree_leaves((path_node,)))
# revealed: list[PathNode]
reveal_type(tree_leaves({"input": path_node}))

# revealed: list[PythonNode]
reveal_type(tree_leaves(python_node))
# revealed: list[PythonNode]
reveal_type(tree_leaves([python_node]))
# revealed: list[PythonNode]
reveal_type(tree_leaves((python_node,)))
# revealed: list[PythonNode]
reveal_type(tree_leaves({"input": python_node}))
```

Current reveals (mypy):

```python only=mypy
from pathlib import Path
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_leaves

path_node = PathNode(path=Path("input.txt"))
python_node = PythonNode(value="input")

# revealed: list[_pytask.nodes.PathNode]
reveal_type(tree_leaves(path_node))
# revealed: list[_pytask.nodes.PathNode]
reveal_type(tree_leaves([path_node]))
# revealed: list[_pytask.nodes.PathNode]
reveal_type(tree_leaves((path_node,)))
# revealed: list[_pytask.nodes.PathNode]
reveal_type(tree_leaves({"input": path_node}))

# revealed: list[_pytask.nodes.PythonNode]
reveal_type(tree_leaves(python_node))
# revealed: list[_pytask.nodes.PythonNode]
reveal_type(tree_leaves([python_node]))
# revealed: list[_pytask.nodes.PythonNode]
reveal_type(tree_leaves((python_node,)))
# revealed: list[_pytask.nodes.PythonNode]
reveal_type(tree_leaves({"input": python_node}))
```


## Flat containers of concrete and provisional node protocols

Intended types:

- `reveal_type(tree_leaves(node))`: `list[PProvisionalNode]`.
- `reveal_type(tree_leaves(nodes))`: `list[PNode | PProvisionalNode]`.
- `reveal_type(tree_leaves(tuple_nodes))`: `list[PNode | PProvisionalNode]`.
- `reveal_type(tree_leaves(named_nodes))`: `list[PNode | PProvisionalNode]`.

Current reveals (ty, pyright, pyrefly):

```python only=ty,pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PNode, PProvisionalNode
from pytask.tree_util import tree_leaves


def check_flat_nodes(
    node: PProvisionalNode,
    nodes: list[PNode | PProvisionalNode],
    tuple_nodes: tuple[PNode | PProvisionalNode, ...],
    named_nodes: dict[str, PNode | PProvisionalNode],
) -> None:
    # revealed: list[PProvisionalNode]
    reveal_type(tree_leaves(node))
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(nodes))
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(tuple_nodes))
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(named_nodes))
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from pytask import PNode, PProvisionalNode
from pytask.tree_util import tree_leaves


def check_flat_nodes(
    node: PProvisionalNode,
    nodes: list[PNode | PProvisionalNode],
    tuple_nodes: tuple[PNode | PProvisionalNode, ...],
    named_nodes: dict[str, PNode | PProvisionalNode],
) -> None:
    # revealed: list[_pytask.node_protocols.PProvisionalNode]
    reveal_type(tree_leaves(node))
    # revealed: list[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode]
    reveal_type(tree_leaves(nodes))
    # revealed: list[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode]
    reveal_type(tree_leaves(tuple_nodes))
    # revealed: list[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode]
    reveal_type(tree_leaves(named_nodes))
```


## Custom leaf predicates retain the general traversal contract

A predicate can treat the entire list as one leaf. Node-container overloads must
not promise individual nodes in that case.

Intended types:

- `reveal_type(tree_leaves(nodes, is_leaf=None))`: `list[PythonNode]`.
- `reveal_type(tree_leaves(nodes, is_leaf=lambda value: isinstance(value, list)))`: `list[list[PythonNode]]`.

Current reveals (ty, pyright, pyrefly):

```python only=ty,pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PythonNode
from pytask.tree_util import tree_leaves

nodes = [PythonNode(value="input")]
# revealed: list[PythonNode]
reveal_type(tree_leaves(nodes, is_leaf=None))
# revealed: list[list[PythonNode]]
reveal_type(tree_leaves(nodes, is_leaf=lambda value: isinstance(value, list)))
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from pytask import PythonNode
from pytask.tree_util import tree_leaves

nodes = [PythonNode(value="input")]
# revealed: list[_pytask.nodes.PythonNode]
reveal_type(tree_leaves(nodes, is_leaf=None))
# revealed: list[list[_pytask.nodes.PythonNode]]
reveal_type(tree_leaves(nodes, is_leaf=lambda value: isinstance(value, list)))
```


## Nested containers of concrete nodes

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [Pyright #9798](https://github.com/microsoft/pyright/issues/9798)

Intended types:

- `reveal_type(tree_leaves(paths))`: `list[PathNode]`.
- `reveal_type(tree_leaves(objects))`: `list[PythonNode]`.

Current reveals (ty, pyright, pyrefly):

```python only=ty,pyright,pyrefly
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

# revealed: list[dict[str, list[tuple[PathNode, ...]]]]
reveal_type(tree_leaves(paths))
# revealed: list[list[dict[str, tuple[PythonNode, ...]]]]
reveal_type(tree_leaves(objects))
```

Current reveals (mypy):

```python only=mypy
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

# revealed: list[dict[str, list[tuple[_pytask.nodes.PathNode, ...]]]]
reveal_type(tree_leaves(paths))
# revealed: list[list[dict[str, tuple[_pytask.nodes.PythonNode, ...]]]]
reveal_type(tree_leaves(objects))
```


## Mixed concrete node types

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [mypy #6751](https://github.com/python/mypy/issues/6751)

Intended types:

- `reveal_type(tree_leaves(nodes))`: `list[PathNode | PythonNode]`.

Current reveals (ty, pyright, pyrefly):

```python only=ty,pyright,pyrefly
from pathlib import Path
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_leaves

nodes: list[PathNode | PythonNode] = [
    PathNode(path=Path("input.txt")),
    PythonNode(value="input"),
]

# revealed: list[PathNode | PythonNode]
reveal_type(tree_leaves(nodes))
```

Current reveals (mypy):

```python only=mypy
from pathlib import Path
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_leaves

nodes: list[PathNode | PythonNode] = [
    PathNode(path=Path("input.txt")),
    PythonNode(value="input"),
]

# revealed: list[_pytask.nodes.PathNode | _pytask.nodes.PythonNode]
reveal_type(tree_leaves(nodes))
```


## Trees annotated with the node protocol

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)

Intended types:

- `reveal_type(leaves)`: `list[PNode]`.
- `reveal_type(node.signature)`: `str`.
- `reveal_type(node.state())`: `str | None`.

Current reveals (ty):

```python only=ty
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_leaves


def check_node_tree(tree: PyTree[PNode]) -> None:
    leaves = tree_leaves(tree)
    # revealed: list[PNode | tuple[PyTree[PNode], ...] | list[PyTree[PNode]] | dict[Any, PyTree[PNode]]]
    reveal_type(leaves)
    for node in leaves:
        # ty-error: [unresolved-attribute]
        # revealed: str
        reveal_type(node.signature)
        # ty-error: [unresolved-attribute]
        # revealed: str | None
        reveal_type(node.state())
        # ty-error: [unresolved-attribute]
        node.load()
```

Current reveals (pyright, pyrefly):

```python only=pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_leaves


def check_node_tree(tree: PyTree[PNode]) -> None:
    leaves = tree_leaves(tree)
    # revealed: list[PNode]
    reveal_type(leaves)
    for node in leaves:
        # ty-error: [unresolved-attribute]
        # revealed: str
        reveal_type(node.signature)
        # ty-error: [unresolved-attribute]
        # revealed: str | None
        reveal_type(node.state())
        # ty-error: [unresolved-attribute]
        node.load()
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_leaves


def check_node_tree(tree: PyTree[PNode]) -> None:
    leaves = tree_leaves(tree)
    # revealed: list[_pytask.node_protocols.PNode]
    reveal_type(leaves)
    for node in leaves:
        # ty-error: [unresolved-attribute]
        # revealed: str
        reveal_type(node.signature)
        # ty-error: [unresolved-attribute]
        # revealed: str | None
        reveal_type(node.state())
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

Intended types:

- `reveal_type(tree_leaves(task.depends_on))`: `list[PNode | PProvisionalNode]`.
- `reveal_type(tree_leaves(task.produces))`: `list[PNode | PProvisionalNode]`.

Current reveals (ty):

```python only=ty
from typing_extensions import reveal_type

from pytask import PTask
from pytask.tree_util import tree_leaves


def check_task_nodes(task: PTask) -> None:
    # mypy-error: [type-var]
    # revealed: list[dict[str, PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]] | PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]]
    reveal_type(tree_leaves(task.depends_on))
    # mypy-error: [type-var]
    # revealed: list[dict[str, PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]] | PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]]
    reveal_type(tree_leaves(task.produces))
```

Current reveals (pyright, pyrefly):

```python only=pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PTask
from pytask.tree_util import tree_leaves


def check_task_nodes(task: PTask) -> None:
    # mypy-error: [type-var]
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(task.depends_on))
    # mypy-error: [type-var]
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(task.produces))
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from pytask import PTask
from pytask.tree_util import tree_leaves


def check_task_nodes(task: PTask) -> None:
    # mypy-error: [type-var]
    # revealed: list[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[..., ...] | list[...] | dict[Any, ...], ...] | list[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[..., ...] | list[...] | dict[Any, ...]] | dict[Any, _pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[..., ...] | list[...] | dict[Any, ...]]]
    reveal_type(tree_leaves(task.depends_on))
    # mypy-error: [type-var]
    # revealed: list[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[..., ...] | list[...] | dict[Any, ...], ...] | list[_pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[..., ...] | list[...] | dict[Any, ...]] | dict[Any, _pytask.node_protocols.PNode | _pytask.node_protocols.PProvisionalNode | tuple[..., ...] | list[...] | dict[Any, ...]]]
    reveal_type(tree_leaves(task.produces))
```


## Discover paths in task nodes

Based on `pytask-latex`'s dependency and product discovery. Narrowing a flattened leaf
to `PPathNode` must allow access to its path without casts or ignores.

Related issues:

- [mypy #6751](https://github.com/python/mypy/issues/6751)
- [mypy #22063](https://github.com/python/mypy/issues/22063)

Intended types:

- `reveal_type(node.path.as_posix())`: `str`.

```python
from typing_extensions import reveal_type

from pytask import PPathNode, PTask
from pytask.tree_util import tree_leaves


def check_task_paths(task: PTask) -> set[str]:
    paths: set[str] = set()
    # mypy-error: [type-var]
    for node in tree_leaves(task.depends_on):
        if isinstance(node, PPathNode):
            # revealed: str
            reveal_type(node.path.as_posix())
            paths.add(node.path.as_posix())
    # mypy-error: [type-var]
    for node in tree_leaves(task.produces):
        if isinstance(node, PPathNode):
            paths.add(node.path.as_posix())
    return paths
```
