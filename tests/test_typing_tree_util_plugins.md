# Tree mapping used by plugins

These snippets reproduce plugin input annotations, callback signatures, and uses of
the results without depending on the plugins. Assignments and return annotations check
recursive result types; reveals check that the outer task argument keys remain strings.
The snippets are static typing tests, not plugin integration tests.

## Load task argument trees with paths

Based on `pytask-parallel`'s `create_kwargs_for_task`. Dependency and product leaves
can be concrete or provisional nodes, and loading them returns arbitrary task values.

Related issues:

- [ty #3415](https://github.com/astral-sh/ty/issues/3415)
- [mypy #22063](https://github.com/python/mypy/issues/22063)

```python
from typing import Any

from pytask import PNode, PProvisionalNode, PTask
from pytask.tree_util import PyTree, tree_map_with_path


def load_node(path: tuple[Any, ...], node: PNode | PProvisionalNode) -> Any:
    return node.load(is_product=path[0] == "produces")


def create_kwargs(task: PTask) -> dict[str, PyTree[Any]]:
    kwargs: dict[str, PyTree[Any]] = {}
    for name, tree in task.depends_on.items():
        kwargs[name] = tree_map_with_path(
            lambda path, node: load_node((name, *path), node), tree
        )
    for name, tree in task.produces.items():
        kwargs[name] = tree_map_with_path(
            lambda path, node: load_node((name, *path), node), tree
        )
    return kwargs
```

## Carry products from a worker

Based on `pytask-parallel`'s product handling. `CarryOverPath` reproduces the plugin's
named tuple declaration. Product mapping changes leaf types and can return `None`.

Related issues:

- [ty #3415](https://github.com/astral-sh/ty/issues/3415)
- [mypy #22063](https://github.com/python/mypy/issues/22063)

Intended types:

- `reveal_type(list(mapped))`: `list[str]`.

```python
from typing import Any, NamedTuple
from typing_extensions import reveal_type

from pytask import PNode, PPathNode, PTask, PythonNode
from pytask.tree_util import PyTree, tree_map_with_path


class CarryOverPath(NamedTuple):
    content: bytes


def carry_product(
    path: tuple[Any, ...], node: PNode
) -> CarryOverPath | PythonNode | None:
    if isinstance(node, PythonNode):
        return node
    if isinstance(node, PPathNode):
        return CarryOverPath(content=node.path.read_bytes())
    return None


def carry_products(task: PTask) -> dict[str, PyTree[CarryOverPath | PythonNode | None]]:
    # mypy-error: [misc] Cannot infer value of type parameter
    mapped = tree_map_with_path(carry_product, task.produces)
    # revealed: list[str]
    reveal_type(list(mapped))
    return mapped
```


## Update products from a corresponding carry-over tree

Based on `pytask-parallel`'s `_update_carry_over_products`. The two trees have
different leaf types. The mapped result must retain its task argument dictionary
and be assignable to `task.produces`.

Related issues:

- [ty #3415](https://github.com/astral-sh/ty/issues/3415)
- [mypy #22063](https://github.com/python/mypy/issues/22063)

Intended types:

- `reveal_type(list(mapped))`: `list[str]`.

```python
from typing import NamedTuple
from typing_extensions import reveal_type

from pytask import PNode, PTask, PythonNode
from pytask.tree_util import PyTree, tree_map


class CarryOverPath(NamedTuple):
    content: bytes


def update_node(node: PNode, carried: CarryOverPath | PythonNode | None) -> PNode:
    if isinstance(carried, PythonNode):
        node.save(carried.load())
    return node


def update_products(
    task: PTask, carried: PyTree[CarryOverPath | PythonNode | None]
) -> None:
    # mypy-error: [misc] Cannot infer value of type parameter
    mapped = tree_map(update_node, task.produces, carried)
    # revealed: list[str]
    reveal_type(list(mapped))
    task.produces = mapped
```


## Resolve remote nodes in task keyword arguments

Based on `pytask-parallel`'s `_write_local_files_to_remote`. The minimal custom node
declares the plugin's `load` return type; other node operations come from `PNode`.
Task values must remain supported even when they are no longer nodes.

Related issues:

- [Pyrefly #4910](https://github.com/facebook/pyrefly/issues/4910)
- [mypy #15750](https://github.com/python/mypy/issues/15750)

Intended types:

- `reveal_type(list(mapped))`: `list[str]`.

Current reveals (ty, pyright):

```python only=ty,pyright
from pathlib import Path
from typing import Any
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_map


class RemotePathNode(PNode):
    def load(self, is_product: bool = False) -> Path:
        raise NotImplementedError


def resolve_remote_values(kwargs: dict[str, PyTree[Any]]) -> dict[str, PyTree[Any]]:
    mapped = tree_map(
        lambda value: value.load() if isinstance(value, RemotePathNode) else value,
        kwargs,
    )
    # revealed: list[str]
    reveal_type(list(mapped))
    return mapped
```

Current reveals (pyrefly):

```python only=pyrefly
from pathlib import Path
from typing import Any
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_map


class RemotePathNode(PNode):
    def load(self, is_product: bool = False) -> Path:
        raise NotImplementedError


def resolve_remote_values(kwargs: dict[str, PyTree[Any]]) -> dict[str, PyTree[Any]]:
    mapped = tree_map(
        lambda value: value.load() if isinstance(value, RemotePathNode) else value,
        kwargs,
    )
    # revealed: list[Unknown]
    reveal_type(list(mapped))
    return mapped
```

Current reveals (mypy):

```python only=mypy
from pathlib import Path
from typing import Any
from typing_extensions import reveal_type

from pytask import PNode
from pytask.tree_util import PyTree, tree_map


class RemotePathNode(PNode):
    def load(self, is_product: bool = False) -> Path:
        raise NotImplementedError


def resolve_remote_values(kwargs: dict[str, PyTree[Any]]) -> dict[str, PyTree[Any]]:
    mapped = tree_map(
        lambda value: value.load() if isinstance(value, RemotePathNode) else value,
        kwargs,
    )
    # revealed: list[Any]
    reveal_type(list(mapped))
    return mapped
```


## Unpack mapped dependencies and products as keyword arguments

Based on the Julia, R, and Stata plugins' keyword argument collection. A path node
becomes a string; other leaves expose their Python value. Both mapped results must
support dictionary unpacking.

Related issues:

- [ty #3415](https://github.com/astral-sh/ty/issues/3415)
- [mypy #15750](https://github.com/python/mypy/issues/15750)

Intended types:

- `reveal_type(list(kwargs))`: `list[str]`.

Current reveals (ty):

```python only=ty
from typing import Any
from typing_extensions import reveal_type

from pytask import PPathNode, PTask
from pytask.tree_util import tree_map


def collect_kwargs(task: PTask) -> dict[str, Any]:
    kwargs = {
        **tree_map(
            lambda node: (
                node.path.as_posix() if isinstance(node, PPathNode) else node.value
            ),
            task.depends_on,
        ),
        **tree_map(
            lambda node: (
                node.path.as_posix() if isinstance(node, PPathNode) else node.value
            ),
            task.produces,
        ),
    }
    # revealed: list[Divergent | str | Unknown]
    reveal_type(list(kwargs))
    return kwargs
```

Current reveals (pyright, pyrefly, mypy):

```python only=pyright,pyrefly,mypy
from typing import Any
from typing_extensions import reveal_type

from pytask import PPathNode, PTask
from pytask.tree_util import tree_map


def collect_kwargs(task: PTask) -> dict[str, Any]:
    kwargs = {
        **tree_map(
            lambda node: (
                node.path.as_posix() if isinstance(node, PPathNode) else node.value
            ),
            task.depends_on,
        ),
        **tree_map(
            lambda node: (
                node.path.as_posix() if isinstance(node, PPathNode) else node.value
            ),
            task.produces,
        ),
    }
    # revealed: list[str]
    reveal_type(list(kwargs))
    return kwargs
```
