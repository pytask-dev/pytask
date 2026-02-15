# Defining dependencies and products

Define task dependencies and products to run your tasks.

Defining dependencies and products also determines task execution order.

This tutorial offers you different interfaces. For type annotations, see the `Annotated`
tabs. You find a tutorial on type hints [here](../type_hints.md).

If you want to avoid type annotations for now, look at the tab named `produces`.

!!! note

    In this tutorial, we only deal with local files. If you want to use pytask with files
    online, S3, GCP, Azure, etc., read the
    [guide on remote files](../how_to_guides/remote_files.md).

First, we focus on defining products that should already be familiar to you. Then, we
focus on how you can declare task dependencies.

We use the same project as before and add a `task_plot_data.py` module.

```text
my_project
│
├───.pytask
│
├───bld
│   ├────data.pkl
│   └────plot.png
│
├───src
│   └───my_project
│       ├────__init__.py
│       ├────config.py
│       ├────task_data_preparation.py
│       └────task_plot_data.py
│
└───pyproject.toml
```

## Products

Let's revisit the task from the [previous tutorial](write_a_task.md) that we defined in
`task_data_preparation.py`.

=== "Annotated"

    ```py hl_lines="8 12"
    --8<-- "docs_src/tutorials/defining_dependencies_products_products_py310.py"
    ```

    [`pytask.Product`](../api/utilities_and_typing.md#pytask.Product) allows marking an
    argument as a product. After the task has finished, pytask will check whether the file
    exists.

=== "produces"

    ```py hl_lines="8"
    --8<-- "docs_src/tutorials/defining_dependencies_products_products_produces.py"
    ```

    Tasks can use `produces` as a "magic" argument name. Every value, or in this case path,
    passed to this argument is automatically treated as a task product. Here, we pass the
    path as the default argument.

!!! tip

    If you do not know about `pathlib` check out this guide by
    [RealPython](https://realpython.com/python-pathlib/). The module is beneficial for
    handling paths conveniently and across platforms.

## Dependencies

Adding a dependency to a task ensures that the dependency is available before execution.

To show how dependencies work, we extend our project with another task that plots the
data generated with `task_create_random_data`. The task is called `task_plot_data`, and
we will define it in `task_plot_data.py`.

=== "Annotated"

    To specify the task relies on `data.pkl`, add the path to the function signature with
    any argument name (here `path_to_data`).

    pytask assumes that all function arguments that do not have a `pytask.Product`
    annotation are dependencies of the task.

    ```py hl_lines="12"
    --8<-- "docs_src/tutorials/defining_dependencies_products_dependencies_py310.py"
    ```

=== "produces"

    To specify that the task relies on the data set `data.pkl`, you can add the path to the
    function signature while choosing any argument name, here `path_to_data`.

    pytask assumes that all function arguments that are not passed to the argument
    `produces` are dependencies of the task.

    ```py hl_lines="9"
    --8<-- "docs_src/tutorials/defining_dependencies_products_dependencies_produces.py"
    ```

Now, let us execute the two paths.

--8<-- "docs/source/_static/md/defining-dependencies-products.md"

## Relative paths

Dependencies and products do not have to be absolute paths. If paths are relative, they
are assumed to point to a location relative to the task module.

=== "Annotated"

    ```py hl_lines="8"
    --8<-- "docs_src/tutorials/defining_dependencies_products_relative_py310.py"
    ```

=== "produces"

    ```py hl_lines="4"
    --8<-- "docs_src/tutorials/defining_dependencies_products_relative_produces.py"
    ```

## Multiple dependencies and products

Of course, tasks can have multiple dependencies and products.

=== "Annotated"

    ```py
    --8<-- "docs_src/tutorials/defining_dependencies_products_multiple1_py310.py"
    ```

    You can group your dependencies and product if you prefer not to have a function
    argument per input. Use dictionaries (recommended), tuples, lists, or more nested
    structures if needed.

    ```py
    --8<-- "docs_src/tutorials/defining_dependencies_products_multiple2_py310.py"
    ```

=== "produces"

    If your task has multiple products, group them in one container like a dictionary
    (recommended), tuples, lists, or more nested structures.

    ```py
    --8<-- "docs_src/tutorials/defining_dependencies_products_multiple1_produces.py"
    ```

    You can do the same with dependencies.

    ```py
    --8<-- "docs_src/tutorials/defining_dependencies_products_multiple2_produces.py"
    ```

<a id="after"></a>

## Depending on a task

In some situations, you want to define a task depending on another task.

pytask allows you to do that, but you lose features like access to paths, which is why
defining dependencies explicitly is always preferred.

There are two modes for it, and both use
[`@task(after=...)`](../api/nodes_and_tasks.md#pytask.task).

First, you can pass the task function or multiple task functions to the decorator.
Applied to the tasks from before, we could have written `task_plot_data` as

```python
@task(after=task_create_random_data)
def task_plot_data(): ...
```

You can also pass a list of task functions.

The second mode is to pass an expression, a substring of the name of the dependent
tasks. Here, we can pass the function name or a significant part of the function name.

```python
@task(after="random_data")
def task_plot_data(): ...
```

You will learn more about expressions in [selecting tasks](selecting_tasks.md).

## Further reading

- There is an additional way to specify products by treating the returns of a task
    function as a product. Read
    [using task returns](../how_to_guides/using_task_returns.md) to learn more about it.
- An overview of all ways to specify dependencies and products and their strengths and
    weaknesses can be found in
    [interfaces for dependencies products](../how_to_guides/interfaces_for_dependencies_products.md).
