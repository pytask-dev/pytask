# Defining dependencies and products

Tasks have dependencies and products that you must define to run your tasks.

Defining dependencies and products also serves another purpose. By analyzing them,
pytask determines the order in which to run the tasks.

This tutorial offers you different interfaces. If you are comfortable with type
annotations or not afraid to try them, look at the `Python 3.10+` or `Python 3.8+` tabs.
You find a tutorial on type hints {doc}`here <../type_hints>`.

If you want to avoid type annotations for now, look at the tab named `produces`.

The `Decorators` tab documents the deprecated approach that should not be used
anymore and will be removed in version v0.5.

In this tutorial, we only deal with local files. If you want to use pytask with files
online, S3, GCP, Azure, etc., read the
{doc}`guide on remote files <../how_to_guides/remote_files>`.

First, we focus on defining products that should already be familiar to you. Then,
we focus on how you can declare task dependencies.

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

Let's revisit the task from the {doc}`previous tutorial <write_a_task>` that we defined
in `task_data_preparation.py`.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_py310.py
:emphasize-lines: 11
```

{class}`~pytask.Product` allows marking an argument as a product. After the
task has finished, pytask will check whether the file exists.

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_py38.py
:emphasize-lines: 11
```

{class}`~pytask.Product` allows marking an argument as a product. After the
task has finished, pytask will check whether the file exists.

:::

:::{tab-item} &#8203;`produces`
:sync: produces

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_produces.py
:emphasize-lines: 8
```

Tasks can use `produces` as a "magic" argument name. Every value, or in this case path,
passed to this argument is automatically treated as a task product. Here, we pass the
path as the default argument.

:::

:::{tab-item} Decorators
:sync: decorators

```{warning}
This approach is deprecated and will be removed in v0.5
```

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_decorators.py
:emphasize-lines: 9, 10
```

The {func}`@pytask.mark.produces <pytask.mark.produces>` marker attaches a product to a
task. After the task has finished, pytask will check whether the file exists.

Add `produces` as an argument of the task function to get access to the same path inside
the task function.

:::
::::

:::{tip}
If you do not know about {mod}`pathlib` check out [^id3] and [^id4]. The module is
beneficial for handling paths conveniently and across platforms.
:::

## Dependencies

Adding a dependency to a task ensures that the dependency is available before execution.

To show how dependencies work, we extend our project with another task that plots the
data generated with `task_create_random_data`. The task is called `task_plot_data`, and
we will define it in `task_plot_data.py`.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

To specify that the task relies on the data set `data.pkl`, you can add the path
to the function signature while choosing any argument name, here `path_to_data`.

pytask assumes that all function arguments that do not have a {class}`~pytask.`Product`
annotation are dependencies of the task.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_dependencies_py310.py
:emphasize-lines: 11
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

To specify that the task relies on the data set `data.pkl`, you can add the path
to the function signature while choosing any argument name, here `path_to_data`.

pytask assumes that all function arguments that do not have the {class}`~pytask.Product`
annotation are dependencies of the task.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_dependencies_py38.py
:emphasize-lines: 11
```

:::

:::{tab-item} &#8203;`produces`
:sync: produces

To specify that the task relies on the data set `data.pkl`, you can add the path to the
function signature while choosing any argument name, here `path_to_data`.

pytask assumes that all function arguments that are not passed to the argument
`produces` are dependencies of the task.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_dependencies_produces.py
:emphasize-lines: 9
```

:::

:::{tab-item} Decorators
:sync: decorators

```{warning}
This approach is deprecated and will be removed in v0.5
```

Equivalent to products, you can use the
{func}`@pytask.mark.depends_on <pytask.mark.depends_on>` decorator to specify that
`data.pkl` is a dependency of the task. Use `depends_on` as a function argument to
access the dependency path inside the function and load the data.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_dependencies_decorators.py
:emphasize-lines: 9, 11
```

:::
::::

Now, let us execute the two paths.

```{include} ../_static/md/defining-dependencies-products.md
```

## Relative paths

Dependencies and products do not have to be absolute paths. If paths are relative, they
are assumed to point to a location relative to the task module.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_relative_py310.py
:emphasize-lines: 8
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_relative_py38.py
:emphasize-lines: 8
```

:::

:::{tab-item} &#8203;`produces`
:sync: produces

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_relative_produces.py
:emphasize-lines: 4
```

:::

:::{tab-item} Decorators
:sync: decorators

```{warning}
This approach is deprecated and will be removed in v0.5
```

You can also use absolute and relative paths as strings that obey the same rules as the
{class}`pathlib.Path`.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_relative_decorators.py
:emphasize-lines: 6
```

If you use `depends_on` or `produces` as arguments for the task function, you will have
access to the paths of the targets as {class}`pathlib.Path`.

:::
::::

## Multiple dependencies and products

Of course, tasks can have multiple dependencies and products.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple1_py310.py
```

You can group your dependencies and product if you prefer not to have a function
argument per input. Use dictionaries (recommended), tuples, lists, or more nested
structures if needed.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple2_py310.py
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple1_py38.py
```

You can group your dependencies and product if you prefer not to have a function
argument per input. Use dictionaries (recommended), tuples, lists, or more nested
structures if needed.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple2_py38.py
```

:::

:::{tab-item} &#8203;`produces`
:sync: produces

If your task has multiple products, group them in one container like a dictionary
(recommended), tuples, lists, or more nested structures.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple1_produces.py
```

You can do the same with dependencies.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple2_produces.py
```

:::

:::{tab-item} Decorators
:sync: decorators

```{warning}
This approach is deprecated and will be removed in v0.5
```

The easiest way to attach multiple dependencies or products to a task is to pass a
{class}`dict` (highly recommended), {class}`list`, or another iterator to the marker
containing the paths.

To assign labels to dependencies or products, pass a dictionary. For example,

```python
from typing import Dict


@pytask.mark.produces({"first": BLD / "data_0.pkl", "second": BLD / "data_1.pkl"})
def task_create_random_data(produces: Dict[str, Path]) -> None:
    ...
```

Then, use `produces` inside the task function.

```pycon
>>> produces["first"]
BLD / "data_0.pkl"

>>> produces["second"]
BLD / "data_1.pkl"
```

You can also use lists and other iterables.

```python
@pytask.mark.produces([BLD / "data_0.pkl", BLD / "data_1.pkl"])
def task_create_random_data(produces):
    ...
```

Inside the function, the arguments `depends_on` or `produces` become a dictionary where
keys are the positions in the list.

```pycon
>>> produces
{0: BLD / "data_0.pkl", 1: BLD / "data_1.pkl"}
```

Why does pytask recommend dictionaries and convert lists, tuples, or other
iterators to dictionaries? First, dictionaries with positions as keys behave very
similarly to lists.

Secondly, dictionary keys are more descriptive and do not assume a fixed
ordering. Both attributes are especially desirable in complex projects.

**Multiple decorators**

pytask merges multiple decorators of one kind into a single dictionary. This might help
you to group dependencies and apply them to multiple tasks.

```python
common_dependencies = pytask.mark.depends_on(
    {"first_text": "text_1.txt", "second_text": "text_2.txt"}
)


@common_dependencies
@pytask.mark.depends_on("text_3.txt")
def task_example(depends_on):
    ...
```

Inside the task, `depends_on` will be

```pycon
>>> depends_on
{"first_text": ... / "text_1.txt", "second_text": "text_2.txt", 0: "text_3.txt"}
```

**Nested dependencies and products**

Dependencies and products can be nested containers consisting of tuples, lists, and
dictionaries. It is beneficial if you want more structure and nesting.

Here is an example of a task that fits some model on data. It depends on a module
containing the code for the model, which is not actively used but ensures that the task
is rerun when the model is changed. And it depends on the data.

```python
@pytask.mark.depends_on(
    {
        "model": [SRC / "models" / "model.py"],
        "data": {"a": SRC / "data" / "a.pkl", "b": SRC / "data" / "b.pkl"},
    }
)
@pytask.mark.produces(BLD / "models" / "fitted_model.pkl")
def task_fit_model(depends_on, produces):
    ...
```

`depends_on` within the function will be

```python
{
    "model": [SRC / "models" / "model.py"],
    "data": {"a": SRC / "data" / "a.pkl", "b": SRC / "data" / "b.pkl"},
}
```

:::
::::

(after)=

## Depending on a task

In some situations, you want to define a task depending on another task.

pytask allows you to do that, but you lose features like access to paths, which is why
defining dependencies explicitly is always preferred.

There are two modes for it, and both use {func}`@task(after=...) <pytask.task>`.

First, you can pass the task function or multiple task functions to the decorator.
Applied to the tasks from before, we could have written `task_plot_data` as

```python
@task(after=task_create_random_data)
def task_plot_data(...):
    ...
```

You can also pass a list of task functions.

The second mode is to pass an expression, a substring of the name of the dependent
tasks. Here, we can pass the function name or a significant part of the function
name.

```python
@task(after="random_data")
def task_plot_data(...):
    ...
```

You will learn more about expressions in {doc}`selecting_tasks`.

## Further reading

- There is an additional way to specify products by treating the returns of a task
  function as a product. Read {doc}`../how_to_guides/using_task_returns` to learn more
  about it.
- An overview of all ways to specify dependencies and products and their strengths and
  weaknesses can be found in
  {doc}`../how_to_guides/interfaces_for_dependencies_products`.

## References

[^id3]: The official documentation for {mod}`pathlib`.

[^id4]: A guide for pathlib by [RealPython](https://realpython.com/python-pathlib/).
