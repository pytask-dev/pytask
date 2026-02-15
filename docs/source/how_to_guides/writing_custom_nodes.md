# Writing custom nodes

In the previous tutorials and how-to guides, you learned that dependencies and products
can be represented as plain Python objects with
[pytask.PythonNode](../api/nodes_and_tasks.md#pytask.PythonNode) or as paths where every
`pathlib.Path` is converted to a
[pytask.PathNode](../api/nodes_and_tasks.md#pytask.PathNode).

In this how-to guide, you will learn about the general concept of nodes and how to write
your own to improve your workflows.

## Use-case

A typical task operation is to load data like a `pandas.DataFrame` from a pickle file,
transform it, and store it on disk. The usual way would be to use paths to point to
inputs and outputs and call `pandas.read_pickle` and `pandas.DataFrame.to_pickle`.

```py
--8<-- "docs_src/how_to_guides/writing_custom_nodes_example_1.py"
```

To remove IO operations from the task and delegate them to pytask, we will replicate the
[pytask.PickleNode](../api/nodes_and_tasks.md#pytask.PickleNode) that automatically
loads and stores Python objects.

And we pass the value to `df` via `typing.Annotated` to preserve the type hint.

The result will be the following task.

=== "Annotated"

    ```py
    --8<-- "docs_src/how_to_guides/writing_custom_nodes_example_2_py310.py"
    ```

=== "Annotated & Return"

    ```py
    --8<-- "docs_src/how_to_guides/writing_custom_nodes_example_2_py310_return.py"
    ```

## Nodes

A custom node needs to follow an interface so that pytask can perform several actions:

- Check whether the node is up-to-date and run the workflow if necessary.
- Load and save values when tasks are executed.

This interface is defined by protocols. A custom node must follow at least the protocol
[pytask.PNode](../api/nodes_and_tasks.md#pytask.PNode) or, even better,
[pytask.PPathNode](../api/nodes_and_tasks.md#pytask.PPathNode) if it is based on a path.
The common node for paths, [pytask.PathNode](../api/nodes_and_tasks.md#pytask.PathNode),
follows the protocol [pytask.PPathNode](../api/nodes_and_tasks.md#pytask.PPathNode).

## `PickleNode`

Since our [pytask.PickleNode](../api/nodes_and_tasks.md#pytask.PickleNode) will only
vary slightly from [pytask.PathNode](../api/nodes_and_tasks.md#pytask.PathNode), we use
it as a template, and with some minor modifications, we arrive at the following class.

```py
--8<-- "docs_src/how_to_guides/writing_custom_nodes_example_3_py310.py"
```

Here are some explanations.

- The node does not need to inherit from the protocol
    [pytask.PPathNode](../api/nodes_and_tasks.md#pytask.PPathNode), but you can do it to
    be more explicit.

- The node has two attributes

    - `name` identifies the node in the DAG, so the name must be unique.
    - `path` holds the path to the file and identifies the node as a path node that is
        handled slightly differently than normal nodes within pytask.

- The node has an additional property that computes the signature of the node. The
    signature is a hash and a unique identifier for the node. For most nodes it will be
    a hash of the path or the name.

- The classmethod
    [pytask.PickleNode.from_path](../api/nodes_and_tasks.md#pytask.PickleNode.from_path)
    is a convenient method to instantiate the class.

- The method `pytask.PickleNode.state` yields a value that signals the node's state. If
    the value changes, pytask knows it needs to regenerate the workflow. We can use the
    timestamp of when the node was last modified.

- pytask calls `pytask.PickleNode.load` when it collects the values of function
    arguments to run the function. The argument `is_product` signals that the node is
    loaded as a product with a
    [pytask.Product](../api/utilities_and_typing.md#pytask.Product) annotation or via
    `produces`.

    When the node is loaded as a dependency, we want to inject the value of the pickle
    file. In the other case, the node returns itself so users can call
    `pytask.PickleNode.save` themselves.

- `pytask.PickleNode.save` is called when a task function returns and allows to save the
    return values.

## Improvements

Usually, you would like your custom node to work with `pathlib.Path` objects and
`upath.UPath` objects allowing to work with remote filesystems. To simplify getting the
state of the node, you can use the `pytask.get_state_of_path` function.

## Conclusion

Nodes are an important in concept pytask. They allow to pytask to build a
[DAG](../glossary.md#dag) and generate a workflow, and they also allow users to extract
IO operations from the task function into the nodes.

pytask only implements two node types,
[pytask.PathNode](../api/nodes_and_tasks.md#pytask.PathNode) and
[pytask.PythonNode](../api/nodes_and_tasks.md#pytask.PythonNode), but many more are
possible. In the future, there should probably be a [plugin](../glossary.md#plugin) that
implements nodes for many other data sources like AWS S3 or databases. See
[Kedro datasets](https://docs.kedro.org/en/stable/kedro_datasets.html) for one example.
