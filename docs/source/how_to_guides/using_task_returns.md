# Using task returns

The tutorial {doc}`../tutorials/defining_dependencies_products` presented different ways
to specify products. What might seem unintuitive at first is that usually one would
associate the return of functions with their products. But, none of the approaches uses
function returns.

This guide shows how you can specify products of tasks via function returns. While being
a potentially more intuitive interface, it allows the user to turn any function, even
third-party functions, into task functions. It also requires more knowledge about
pytask's internals which is why it is not suitable as a tutorial.

## Return type annotations

One way to declare the returns of functions as products is annotating the return type.
In the following example, the second value of {class}`typing.Annotated` is a path that
defines where the return of the function, a string, should be stored.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_1_py310.py
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_1_py38.py
```

:::
::::

It works because internally the path is converted to a {class}`pytask.PathNode` that is
able to store objects of type {class}`str` and {class}`bytes`.

:::{seealso}
Read the explanation on {doc}`nodes <../how_to_guides/writing_custom_nodes>` to learn
more about how nodes work.
:::

## Task decorator

In case you are not able to set a return type annotation to the task function, for
example, because it is a lambda or a third-party function, you can use
{func}`@pytask.task(produces=...) <pytask.task>`.

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_2_task.py
```

## Multiple returns

If a task function has multiple returns, you can use multiple nodes to store each of the
returns in a different place. The following example shows how to accomplish it with both
of the previous interfaces.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_3_py310.py
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_3_py38.py
```

:::

:::{tab-item} &#8203;`@pytask.task`

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_3_task.py
```

:::
::::

Each return is mapped to its node by respecting its position in the tuple.

In fact, any {term}`PyTree` can be used. The only requirement is that the PyTree of
nodes defined to capture the function returns has the same structure as the returns or
is a shallower tree.

The following example shows how a task function with a complex structure of returns is
mapped to the defined nodes.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_4_py310.py
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_4_py38.py
```

:::

:::{tab-item} &#8203;`@pytask.task`

```{literalinclude} ../../../docs_src/how_to_guides/using_task_returns_example_4_task.py
```

:::
::::

The returns are mapped to the nodes as follows.

```python
PythonNode(name="dict1") <- "a"
PythonNode(name="dict2") <- {"b": 1, "c": 2}
PythonNode(name="tuple1") <- 3
PythonNode(name="tuple2") <- 4
PythonNode(name="int") <- 5
```
