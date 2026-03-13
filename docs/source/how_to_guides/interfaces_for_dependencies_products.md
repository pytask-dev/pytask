# Interfaces for dependencies and products

Different interfaces exist for dependencies and products, and it might not be obvious
when to use what. This guide gives you an overview of the different strengths of each
approach.

## Legend

- ✅ = True
- ❌ = False
- ➖ = Does not apply

## Dependencies

In general, pytask regards everything as a task dependency if it is not marked as a
product. Thus, you can also think of the following examples as how to inject values into
a task. When we talk about products later, the same interfaces will be used.

|                                         | `def task(arg: ... = ...)` | `Annotated[..., value]` | `@task(kwargs=...)` |
| --------------------------------------- | :------------------------: | :---------------------: | :-----------------: |
| No type annotations required            |             ✅             |           ❌            |         ✅          |
| Flexible choice of argument name        |             ✅             |           ✅            |         ✅          |
| Supports third-party functions as tasks |             ❌             |           ❌            |         ✅          |

<a id="default-argument"></a>

### Default argument

You can pass a value to a task as a default argument.

```py
--8<-- "docs_src/how_to_guides/interfaces/dependencies_default.py"
```

<a id="annotation"></a>

### Annotation with value

It is possible to include the value in the type annotation.

It is especially helpful if you pass a
[pytask.PNode](../api/nodes_and_tasks.md#pytask.PNode) to the task. If you passed a node
as the default argument, type checkers like mypy would expect the node to enter the
task, but the value injected into the task depends on the nodes
[pytask.PNode.load](../api/nodes_and_tasks.md#pytask.PNode.load) method. For a
[pytask.PathNode](../api/nodes_and_tasks.md#pytask.PathNode)

```py
--8<-- "docs_src/how_to_guides/interfaces/dependencies_annotation.py"
```

<a id="task-kwargs"></a>

### `@task(kwargs=...)`

You can use the `kwargs` argument of the `@task` decorator to pass a dictionary. It
applies to dependencies and products alike.

```py
--8<-- "docs_src/how_to_guides/interfaces/dependencies_task_kwargs.py"
```

## Products

|                                                           | `def task(arg: Annotated[..., Product] = ...)` | `Annotated[..., value, Product]` | `produces` | `@task(produces=...)` | `def task() -> Annotated[..., value]` |
| --------------------------------------------------------- | :--------------------------------------------: | :------------------------------: | :--------: | :-------------------: | :-----------------------------------: |
| No type annotations required                              |                       ❌                       |                ❌                |     ✅     |          ✅           |                  ❌                   |
| Flexible choice of argument name                          |                       ✅                       |                ✅                |     ❌     |          ✅           |                  ➖                   |
| Supports third-party functions as tasks                   |                       ❌                       |                ❌                |     ❌     |          ✅           |                  ❌                   |
| Allows to pass custom node while preserving type of value |                       ❌                       |                ✅                |     ✅     |          ✅           |                  ✅                   |

### `Product` annotation

The syntax is the same as [default argument](#default-argument), but the
[pytask.Product](../api/utilities_and_typing.md#pytask.Product) annotation turns the
argument into a task product.

```py
--8<-- "docs_src/how_to_guides/interfaces/products_annotation.py"
```

### `Product` annotation with value

The syntax is the same as [annotation](#annotation), but the
[pytask.Product](../api/utilities_and_typing.md#pytask.Product) annotation turns the
argument into a task product.

```py
--8<-- "docs_src/how_to_guides/interfaces/products_annotation_with_pnode.py"
```

### `produces`

Without using any type annotation, you can use `produces` as a magical argument name to
treat every value passed to it as a task product.

```py
--8<-- "docs_src/how_to_guides/interfaces/products_produces.py"
```

<a id="return-annotation"></a>

### Return annotation

You can also add a node or a value that will be parsed to a node to the annotation of
the return type. It allows us to treat the returns of the task function as products.

```py
--8<-- "docs_src/how_to_guides/interfaces/products_return_annotation.py"
```

<a id="task-produces"></a>

### `@task(produces=...)`

In situations where the task return is the product like
[return annotation](#return-annotation), but you cannot modify the type annotation of
the return, use the argument `produces` of the `@task` decorator.

Pass the node or value you otherwise include in the type annotation to `produces`.

```py
--8<-- "docs_src/how_to_guides/interfaces/products_task_produces.py"
```
