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

```python
from typing import Any
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PTask
from pytask.tree_util import PyTree, tree_structure


def check_task_structures(task: PTask, out: Any, carried: PyTree[Any]) -> None:
    output: PyTreeSpec = tree_structure(out)
    declared: PyTreeSpec = tree_structure(task.produces["return"])
    reveal_type(declared.is_prefix(output, strict=False))  # revealed: bool
    products: PyTreeSpec = tree_structure(task.produces)
    worker_products: PyTreeSpec = tree_structure(carried)
    reveal_type(products.is_prefix(worker_products, strict=False))  # revealed: bool
    dependencies: PyTreeSpec = tree_structure(task.depends_on)
```

# tree_flatten_with_path

Flattening must preserve node leaf types and expose paths and a usable structure.

## Concrete nodes in different containers

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)

```python
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PathNode, PythonNode
from pytask.tree_util import tree_flatten_with_path


def check_flattened_nodes(path_node: PathNode, python_node: PythonNode) -> None:
    paths, leaves, spec = tree_flatten_with_path(path_node)
    reveal_type(paths)  # revealed: list[tuple[Any, ...]]
    reveal_type(leaves)  # revealed: list[PathNode]
    structure: PyTreeSpec = spec
    reveal_type(tree_flatten_with_path([path_node])[1])  # revealed: list[PathNode]
    reveal_type(tree_flatten_with_path((path_node,))[1])  # revealed: list[PathNode]
    # revealed: list[PathNode]
    reveal_type(tree_flatten_with_path({"input": path_node})[1])
    reveal_type(tree_flatten_with_path(python_node)[1])  # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path([python_node])[1])  # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path((python_node,))[1])  # revealed: list[PythonNode]
    # revealed: list[PythonNode]
    reveal_type(tree_flatten_with_path({"input": python_node})[1])
```

## Nested containers of concrete nodes

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [Pyright #9798](https://github.com/microsoft/pyright/issues/9798)

```python
from typing_extensions import reveal_type

from pytask import PathNode, PythonNode
from pytask.tree_util import tree_flatten_with_path


def check_nested_nodes(
    paths: dict[str, list[tuple[PathNode, ...]]],
    objects: list[dict[str, tuple[PythonNode, ...]]],
) -> None:
    reveal_type(tree_flatten_with_path(paths)[1])  # revealed: list[PathNode]
    reveal_type(tree_flatten_with_path(objects)[1])  # revealed: list[PythonNode]
```

## Protocol trees and task dependencies and products

Related issues:

- [ty #2870](https://github.com/astral-sh/ty/issues/2870)
- [mypy #6751](https://github.com/python/mypy/issues/6751)

```python
from typing_extensions import reveal_type

from pytask import PNode, PTask
from pytask.tree_util import PyTree, tree_flatten_with_path


def check_protocol_trees(tree: PyTree[PNode], task: PTask) -> None:
    paths, leaves, spec = tree_flatten_with_path(tree)
    reveal_type(paths)  # revealed: list[tuple[Any, ...]]
    reveal_type(leaves)  # revealed: list[PNode]
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_flatten_with_path(task.depends_on)[1])
    # mypy-error: [misc] Cannot infer value of type parameter
    # revealed: list[PNode | PProvisionalNode]
    reveal_type(tree_flatten_with_path(task.produces)[1])
```

## A custom predicate can make a container a leaf

```python
from typing_extensions import reveal_type

from optree import PyTreeSpec
from pytask import PythonNode
from pytask.tree_util import tree_flatten_with_path, tree_structure


def check_container_leaf(nodes: list[PythonNode]) -> None:
    paths, leaves, spec = tree_flatten_with_path(
        nodes, is_leaf=lambda value: isinstance(value, list)
    )
    reveal_type(paths)  # revealed: list[tuple[Any, ...]]
    reveal_type(leaves)  # revealed: list[list[PythonNode]]
    structure: PyTreeSpec = tree_structure(
        nodes, is_leaf=lambda value: isinstance(value, list)
    )
    reveal_type(structure.is_prefix(spec, strict=False))  # revealed: bool
```
