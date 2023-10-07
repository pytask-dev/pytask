# Writing custom nodes

In the previous tutorials and how-to guides, you learned that dependencies and products
can be represented as plain Python objects with {class}`pytask.PythonNode` or as paths
where every {class}`pathlib.Path` is converted to a {class}`pytask.PathNode`.

In this how-to guide, you will learn about the general concept of nodes and how to write
your own to improve your workflows.

## Use-case

A typical task operation is to load data like a {class}`pandas.DataFrame` from a pickle
file, transform it, and store it on disk. The usual way would be to use paths to point
to inputs and outputs and call {func}`pandas.read_pickle` and
{meth}`pandas.DataFrame.to_pickle`.

```{literalinclude} ../../../docs_src/how_to_guides/writing_custom_nodes_example_1.py
```

To remove IO operations from the task and delegate them to pytask, we will write a
`PickleNode` that automatically loads and stores Python objects.

We will also use the feature explained in {doc}`using_task_returns` to define products
of the task function via the function's return value.

And we pass the value to `df` via {obj}`Annotated` to preserve the type hint.

The result will be the following task.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/how_to_guides/writing_custom_nodes_example_2_py310.py
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/how_to_guides/writing_custom_nodes_example_2_py38.py
```

:::
::::

## Nodes

A custom node needs to follow an interface so that pytask can perform several actions:

- Check whether the node is up-to-date and run the workflow if necessary.
- Load and save values when tasks are executed.

This interface is defined by protocols [^structural-subtyping]. A custom node must
follow at least the protocol {class}`pytask.PNode` or, even better,
{class}`pytask.PPathNode` if it is based on a path. The common node for paths,
{class}`pytask.PathNode`, follows the protocol {class}`pytask.PPathNode`.

## `PickleNode`

Since our {class}`PickleNode` will only vary slightly from {class}`pytask.PathNode`, we
use it as a template, and with some minor modifications, we arrive at the following
class.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/how_to_guides/writing_custom_nodes_example_3_py310.py
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/how_to_guides/writing_custom_nodes_example_3_py38.py
```

:::
::::

Here are some explanations.

- The node does not need to inherit from the protocol {class}`pytask.PPathNode`, but you
  can do it to be more explicit.
- The node has two attributes
  - `name` identifies the node in the DAG, so the name must be unique.
  - `path` holds the path to the file and identifies the node as a path node that is
    handled slightly differently than normal nodes within pytask.
- The {func}`classmethod` {meth}`PickleNode.from_path` is a convenient method to
  instantiate the class.
- The method {meth}`PickleNode.state` yields a value that signals the node's state. If
  the value changes, pytask knows it needs to regenerate the workflow. We can use
  the timestamp of when the node was last modified.
- pytask calls {meth}`PickleNode.load` when it collects the values of function arguments
  to run the function. In our example, we read the file and unpickle the data.
- {meth}`PickleNode.save` is called when a task function returns and allows to save the
  return values.

## Conclusion

Nodes are an important in concept pytask. They allow to pytask to build a DAG and
generate a workflow, and they also allow users to extract IO operations from the task
function into the nodes.

pytask only implements two node types, {class}`PathNode` and {class}`PythonNode`, but
many more are possible. In the future, there should probably be a plugin that implements
nodes for many other data sources like AWS S3 or databases. [^kedro]

## References

[^structural-subtyping]:
    Structural subtyping is similar to ABCs an approach in Python to
    enforce interfaces, but it can be considered more pythonic since it is closer to
    duck typing. Hynek Schlawack wrote a comprehensive
    [guide on subclassing](https://hynek.me/articles/python-subclassing-redux/) that
    features protocols under "Type 2". Glyph wrote an introduction to protocols called
    [I want a new duck](https://glyph.twistedmatrix.com/2020/07/new-duck.html).

[^kedro]:
    Kedro, another workflow system, provides many adapters to data sources:
    https://docs.kedro.org/en/stable/kedro_datasets.html.
