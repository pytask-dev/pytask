# Defining dependencies and products

To ensure pytask executes all tasks in the correct order, define which dependencies are
required and which products are produced by a task.

:::{important}
If you do not specify dependencies and products as explained below, pytask will not be
able to build a graph, a {term}`DAG`, and will not be able to execute all tasks in the
project correctly!
:::

## Products

Let's revisit the task from the {doc}`previous tutorial <write_a_task>`.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_py310.py
:emphasize-lines: 11
```

{class}`~pytask.Product` allows to declare an argument as a product. After the
task has finished, pytask will check whether the file exists.

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_py38.py
:emphasize-lines: 11
```

Using {class}`~pytask.Product` allows to declare an argument as a product. After the
task has finished, pytask will check whether the file exists.

:::

:::{tab-item} Decorators
:sync: decorators

```{warning}
This approach is deprecated and will be removed in v0.5
```

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_decorators.py
:emphasize-lines: 9, 10
```

The {func}`@pytask.mark.produces <pytask.mark.produces>` marker attaches a
product to a task which is a {class}`pathlib.Path` to file. After the task has finished,
pytask will check whether the file exists.

Optionally, you can use `produces` as an argument of the task function and get access to
the same path inside the task function.

:::
::::

:::{tip}
If you do not know about {mod}`pathlib` check out [^id3] and [^id4]. The module is
beneficial for handling paths conveniently and across platforms.
:::

## Dependencies

Most tasks have dependencies and it is important to specify. Then, pytask ensures that
the dependencies are available before executing the task.

In the example you see a task that creates a plot while relying on some data set.

::::{tab-set}

:::{tab-item} Python 3.10+
:sync: python310plus

To specify that the task relies on the data set `data.pkl`, you can simply add the path
to the function signature while choosing any argument name, here `path_to_data`.

pytask assumes that all function arguments that do not have the {class}`~pytask.Product`
annotation are dependencies of the task.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_dependencies_py310.py
:emphasize-lines: 9
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

To specify that the task relies on the data set `data.pkl`, you can simply add the path
to the function signature while choosing any argument name, here `path_to_data`.

pytask assumes that all function arguments that do not have the {class}`~pytask.Product`
annotation are dependencies of the task.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_dependencies_py38.py
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
:emphasize-lines: 7, 9
```

:::
::::

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

You can group your dependencies and product if you prefer not having a function argument
per input. Use dictionaries (recommended), tuples, lists, or more nested structures if
you need.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple2_py310.py
```

:::

:::{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple1_py38.py
```

You can group your dependencies and product if you prefer not having a function argument
per input. Use dictionaries (recommended), tuples, lists, or more nested structures if
you need.

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_multiple2_py38.py
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

Secondly, dictionaries use keys instead of positions that are more verbose and
descriptive and do not assume a fixed ordering. Both attributes are especially desirable
in complex projects.

## Multiple decorators

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

## Nested dependencies and products

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


## References

[^id3]: The official documentation for {mod}`pathlib`.

[^id4]: A guide for pathlib by [RealPython](https://realpython.com/python-pathlib/).
