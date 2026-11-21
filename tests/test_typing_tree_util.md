# tree_leaves

The cases below document the intended leaf types for pytask node trees. When a
checker infers a different type, the snapshot records its current output so
changes can be reviewed against the intended type.

## Flat dictionary of concrete nodes

The intended type is `list[PathNode]`. Ty and mypy can infer the entire dictionary
as the leaf. See [ty #2870](https://github.com/astral-sh/ty/issues/2870).

```python only=ty
from typing_extensions import reveal_type

from pytask import PathNode
from pytask.tree_util import tree_leaves


def check_flat_dict(node: PathNode) -> None:
    # revealed: list[dict[str, PathNode]]
    reveal_type(tree_leaves({"input": node}))
```

```python only=pyright,pyrefly
from typing_extensions import assert_type

from pytask import PathNode
from pytask.tree_util import tree_leaves


def check_flat_dict(node: PathNode) -> None:
    assert_type(tree_leaves({"input": node}), list[PathNode])
```

```python only=mypy
from typing_extensions import reveal_type

from pytask import PathNode
from pytask.tree_util import tree_leaves


def check_flat_dict(node: PathNode) -> None:
    # revealed: list[dict[Any, _pytask.nodes.PathNode]]
    reveal_type(tree_leaves({"input": node}))
```

## Custom leaf predicates can treat a container as a leaf

When the predicate accepts the whole input, the intended leaf type is the
container type, `list[PythonNode]`.

```python only=ty,pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PythonNode
from pytask.tree_util import tree_leaves

nodes = [PythonNode(value="input")]
# revealed: list[list[PythonNode]]
reveal_type(tree_leaves(nodes, is_leaf=lambda value: isinstance(value, list)))
```

```python only=mypy
from typing_extensions import reveal_type

from pytask import PythonNode
from pytask.tree_util import tree_leaves

nodes = [PythonNode(value="input")]
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


## Trees annotated with the node protocol

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)

Intended types:

- `reveal_type(leaves)`: `list[PNode]`.
- `reveal_type(node.signature)`: `str`.
- `reveal_type(node.state())`: `str | None`.

Current reveals (ty):

Ty reports these attribute errors as `unresolved-attribute` in 0.0.91 and
`missing-union-attribute` in 0.0.107.

```python only=ty
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_leaves


def check_node_tree(tree: PyTree[PNode]) -> None:
    leaves = tree_leaves(tree)
    # revealed: list[PNode | tuple[PyTree[PNode], ...] | list[PyTree[PNode]] | dict[Any, PyTree[PNode]]]
    reveal_type(leaves)
    for node in leaves:
        # revealed: str
        reveal_type(node.signature)  # type: ignore
        # revealed: str | None
        reveal_type(node.state())  # type: ignore
        node.load()  # type: ignore
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
    # revealed: list[dict[str, PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]] | PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]]
    reveal_type(tree_leaves(task.depends_on))
    # revealed: list[dict[str, PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]] | PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]]
    reveal_type(tree_leaves(task.produces))
```

Current reveals (pyright, pyrefly):

```python only=pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PTask
from pytask.tree_util import tree_leaves


def check_task_nodes(task: PTask) -> None:
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(task.depends_on))
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_leaves(task.produces))
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from pytask import PTask
from pytask.tree_util import tree_leaves


def check_task_nodes(task: PTask) -> None:
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[Any]
    reveal_type(tree_leaves(task.depends_on))
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[Any]
    reveal_type(tree_leaves(task.produces))
```


## Discover paths in task nodes

Based on `pytask-latex`'s dependency and product discovery. Narrowing a flattened leaf
to `PPathNode` must allow access to its path without casts or ignores.

Related issues:

- [mypy #6751](https://github.com/python/mypy/issues/6751)
- [mypy #22063](https://github.com/python/mypy/issues/22063)

Intended types:

- The narrowed path's `as_posix()` result is `str`.

```python
from typing_extensions import assert_type

from pytask import PPathNode, PTask
from pytask.tree_util import tree_leaves


def check_task_paths(task: PTask) -> set[str]:
    paths: set[str] = set()
    # mypy-error: [misc] Cannot infer value of type parameter
    for node in tree_leaves(task.depends_on):
        if isinstance(node, PPathNode):
            assert_type(node.path.as_posix(), str)
            paths.add(node.path.as_posix())
    # mypy-error: [misc] Cannot infer value of type parameter
    for node in tree_leaves(task.produces):
        if isinstance(node, PPathNode):
            paths.add(node.path.as_posix())
    return paths
```
