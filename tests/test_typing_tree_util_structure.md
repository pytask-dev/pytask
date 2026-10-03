# tree_structure

Structure queries must accept node trees and return a usable `PyTreeSpec`, without
requiring casts of task dependencies or products.

## Concrete nodes in flat and nested containers

```python
from optree import PyTreeSpec
from pytask import PathNode, PythonNode
from pytask.tree_util import tree_structure


def check_structures(path_node: PathNode, python_node: PythonNode) -> None:
    single: PyTreeSpec = tree_structure(path_node)
    listed: PyTreeSpec = tree_structure([python_node])
    paired: PyTreeSpec = tree_structure((path_node, python_node))
    named: PyTreeSpec = tree_structure({"input": path_node})
    nested: PyTreeSpec = tree_structure({"inputs": [(path_node, python_node)]})
```

## Compare task return and worker product structures

Based on pytask's return validation and pytask-parallel's return validation and
carry-over product updates. The comparison must work without casting either tree.

Intended types:

- `reveal_type(declared.is_prefix(output, strict=False))`: `bool`.
- `reveal_type(products.is_prefix(worker_products, strict=False))`: `bool`.

```python
from typing import Any
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PTask
from pytask.tree_util import PyTree, tree_structure


def check_task_structures(task: PTask, out: Any, carried: PyTree[Any]) -> None:
    output: PyTreeSpec = tree_structure(out)
    declared: PyTreeSpec = tree_structure(task.produces["return"])
    # revealed: bool
    reveal_type(declared.is_prefix(output, strict=False))
    products: PyTreeSpec = tree_structure(task.produces)
    worker_products: PyTreeSpec = tree_structure(carried)
    # revealed: bool
    reveal_type(products.is_prefix(worker_products, strict=False))
    dependencies: PyTreeSpec = tree_structure(task.depends_on)
```


# tree_flatten_with_path

Flattening must preserve node leaf types and expose paths and a usable structure.

## Concrete nodes in different containers

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)

Intended types:

- `reveal_type(paths)`: `list[tuple[Any, ...]]`.
- `reveal_type(leaves)`: `list[PathNode]`.
- `reveal_type(tree_flatten_with_path([path_node])[1])`: `list[PathNode]`.
- `reveal_type(tree_flatten_with_path((path_node,))[1])`: `list[PathNode]`.
- `reveal_type(tree_flatten_with_path({"input": path_node})[1])`: `list[PathNode]`.
- `reveal_type(tree_flatten_with_path(python_node)[1])`: `list[PythonNode]`.
- `reveal_type(tree_flatten_with_path([python_node])[1])`: `list[PythonNode]`.
- `reveal_type(tree_flatten_with_path((python_node,))[1])`: `list[PythonNode]`.
- `reveal_type(tree_flatten_with_path({"input": python_node})[1])`: `list[PythonNode]`.

Current reveals (ty):

```python only=ty
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PathNode, PythonNode
from pytask.tree_util import tree_flatten_with_path


def check_flattened_nodes(path_node: PathNode, python_node: PythonNode) -> None:
    paths, leaves, spec = tree_flatten_with_path(path_node)
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[PathNode]
    reveal_type(leaves)
    structure: PyTreeSpec = spec
    # revealed: list[list[PathNode]]
    reveal_type(tree_flatten_with_path([path_node])[1])
    # revealed: list[tuple[PathNode] | PathNode]
    reveal_type(tree_flatten_with_path((path_node,))[1])
    # revealed: list[dict[str, PathNode]]
    reveal_type(tree_flatten_with_path({"input": path_node})[1])
    # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path(python_node)[1])
    # revealed: list[list[PythonNode]]
    reveal_type(tree_flatten_with_path([python_node])[1])
    # revealed: list[tuple[PythonNode] | PythonNode]
    reveal_type(tree_flatten_with_path((python_node,))[1])
    # revealed: list[dict[str, PythonNode]]
    reveal_type(tree_flatten_with_path({"input": python_node})[1])
```

Current reveals (pyright, pyrefly):

```python only=pyright,pyrefly
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PathNode, PythonNode
from pytask.tree_util import tree_flatten_with_path


def check_flattened_nodes(path_node: PathNode, python_node: PythonNode) -> None:
    paths, leaves, spec = tree_flatten_with_path(path_node)
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[PathNode]
    reveal_type(leaves)
    structure: PyTreeSpec = spec
    # revealed: list[PathNode]
    reveal_type(tree_flatten_with_path([path_node])[1])
    # revealed: list[PathNode]
    reveal_type(tree_flatten_with_path((path_node,))[1])
    # revealed: list[PathNode]
    reveal_type(tree_flatten_with_path({"input": path_node})[1])
    # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path(python_node)[1])
    # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path([python_node])[1])
    # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path((python_node,))[1])
    # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path({"input": python_node})[1])
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PathNode, PythonNode
from pytask.tree_util import tree_flatten_with_path


def check_flattened_nodes(path_node: PathNode, python_node: PythonNode) -> None:
    paths, leaves, spec = tree_flatten_with_path(path_node)
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[_pytask.nodes.PathNode]
    reveal_type(leaves)
    structure: PyTreeSpec = spec
    # revealed: list[list[_pytask.nodes.PathNode]]
    reveal_type(tree_flatten_with_path([path_node])[1])
    # revealed: list[_pytask.nodes.PathNode]
    reveal_type(tree_flatten_with_path((path_node,))[1])
    # revealed: list[dict[Any, _pytask.nodes.PathNode]]
    reveal_type(tree_flatten_with_path({"input": path_node})[1])
    # revealed: list[_pytask.nodes.PythonNode]
    reveal_type(tree_flatten_with_path(python_node)[1])
    # revealed: list[list[_pytask.nodes.PythonNode]]
    reveal_type(tree_flatten_with_path([python_node])[1])
    # revealed: list[_pytask.nodes.PythonNode]
    reveal_type(tree_flatten_with_path((python_node,))[1])
    # revealed: list[dict[Any, _pytask.nodes.PythonNode]]
    reveal_type(tree_flatten_with_path({"input": python_node})[1])
```


## Nested containers of concrete nodes

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [Pyright #9798](https://github.com/microsoft/pyright/issues/9798)

Intended types:

- `reveal_type(tree_flatten_with_path(paths)[1])`: `list[PathNode]`.
- `reveal_type(tree_flatten_with_path(objects)[1])`: `list[PythonNode]`.

Current reveals (ty, pyright, pyrefly):

```python only=ty,pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_flatten_with_path


def check_nested_nodes(
    paths: dict[str, list[tuple[PathNode, ...]]],
    objects: list[dict[str, tuple[PythonNode, ...]]],
) -> None:
    # revealed: list[dict[str, list[tuple[PathNode, ...]]]]
    reveal_type(tree_flatten_with_path(paths)[1])
    # revealed: list[list[dict[str, tuple[PythonNode, ...]]]]
    reveal_type(tree_flatten_with_path(objects)[1])
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_flatten_with_path


def check_nested_nodes(
    paths: dict[str, list[tuple[PathNode, ...]]],
    objects: list[dict[str, tuple[PythonNode, ...]]],
) -> None:
    # revealed: list[dict[str, list[tuple[_pytask.nodes.PathNode, ...]]]]
    reveal_type(tree_flatten_with_path(paths)[1])
    # revealed: list[list[dict[str, tuple[_pytask.nodes.PythonNode, ...]]]]
    reveal_type(tree_flatten_with_path(objects)[1])
```


## Protocol trees and task dependencies and products

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [mypy #6751](https://github.com/python/mypy/issues/6751)

Intended types:

- `reveal_type(paths)`: `list[tuple[Any, ...]]`.
- `reveal_type(leaves)`: `list[PNode]`.
- `reveal_type(tree_flatten_with_path(task.depends_on)[1])`: `list[PNode | PProvisionalNode]`.
- `reveal_type(tree_flatten_with_path(task.produces)[1])`: `list[PNode | PProvisionalNode]`.

Current reveals (ty):

```python only=ty
from typing_extensions import reveal_type

from pytask import PNode, PTask
from pytask.tree_util import PyTree, tree_flatten_with_path


def check_protocol_trees(tree: PyTree[PNode], task: PTask) -> None:
    paths, leaves, spec = tree_flatten_with_path(tree)
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[PNode | tuple[PyTree[PNode], ...] | list[PyTree[PNode]] | dict[Any, PyTree[PNode]]]
    reveal_type(leaves)
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[dict[str, PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]] | PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]]
    reveal_type(tree_flatten_with_path(task.depends_on)[1])
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[dict[str, PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]] | PNode | PProvisionalNode | tuple[PyTree[PNode | PProvisionalNode], ...] | list[PyTree[PNode | PProvisionalNode]] | dict[Any, PyTree[PNode | PProvisionalNode]]]
    reveal_type(tree_flatten_with_path(task.produces)[1])
```

Current reveals (pyright, pyrefly):

```python only=pyright,pyrefly
from typing_extensions import reveal_type

from pytask import PNode, PTask
from pytask.tree_util import PyTree, tree_flatten_with_path


def check_protocol_trees(tree: PyTree[PNode], task: PTask) -> None:
    paths, leaves, spec = tree_flatten_with_path(tree)
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[PNode]
    reveal_type(leaves)
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_flatten_with_path(task.depends_on)[1])
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_flatten_with_path(task.produces)[1])
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from pytask import PNode, PTask
from pytask.tree_util import PyTree, tree_flatten_with_path


def check_protocol_trees(tree: PyTree[PNode], task: PTask) -> None:
    paths, leaves, spec = tree_flatten_with_path(tree)
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[_pytask.node_protocols.PNode]
    reveal_type(leaves)
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[Any]
    reveal_type(tree_flatten_with_path(task.depends_on)[1])
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[Any]
    reveal_type(tree_flatten_with_path(task.produces)[1])
```


## A custom predicate can make a container a leaf

Intended types:

- `reveal_type(paths)`: `list[tuple[Any, ...]]`.
- `reveal_type(leaves)`: `list[list[PythonNode]]`.
- `reveal_type(structure.is_prefix(spec, strict=False))`: `bool`.

Current reveals (ty, pyright, pyrefly):

```python only=ty,pyright,pyrefly
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PythonNode
from pytask.tree_util import tree_flatten_with_path, tree_structure


def check_container_leaf(nodes: list[PythonNode]) -> None:
    paths, leaves, spec = tree_flatten_with_path(
        nodes, is_leaf=lambda value: isinstance(value, list)
    )
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[list[PythonNode]]
    reveal_type(leaves)
    structure: PyTreeSpec = tree_structure(
        nodes, is_leaf=lambda value: isinstance(value, list)
    )
    # revealed: bool
    reveal_type(structure.is_prefix(spec, strict=False))
```

Current reveals (mypy):

```python only=mypy
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PythonNode
from pytask.tree_util import tree_flatten_with_path, tree_structure


def check_container_leaf(nodes: list[PythonNode]) -> None:
    paths, leaves, spec = tree_flatten_with_path(
        nodes, is_leaf=lambda value: isinstance(value, list)
    )
    # revealed: list[tuple[Any, ...]]
    reveal_type(paths)
    # revealed: list[list[_pytask.nodes.PythonNode]]
    reveal_type(leaves)
    structure: PyTreeSpec = tree_structure(
        nodes, is_leaf=lambda value: isinstance(value, list)
    )
    # revealed: bool
    reveal_type(structure.is_prefix(spec, strict=False))
```
