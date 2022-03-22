# Defining dependencies and products

To ensure pytask executes all tasks in a correct order, define which dependencies are
required and which products are produced by a task.

:::{important}
If you do not specify dependencies and products as explained below, pytask will not able
to build a graph, a {term}`DAG`, and will not be able to execute all tasks in the
project correctly!
:::

## Products

Let's revisit the task from the {doc}`previous tutorial <write_a_task>`.

```python
@pytask.mark.produces(BLD / "data.pkl")
def task_create_random_data(produces):
    ...
```

The {func}`@pytask.mark.produces <_pytask.collect_utils.produces>` marker attaches a product to
a task which is a {class}`pathlib.Path` to file. After the task has finished, pytask
will check whether the file exists.

Optionally, you can use `produces` as an argument of the task function and get access to
the same path inside the task function.

:::{tip}
If you do not know about {mod}`pathlib` check out [^id3] and [^id4]. The module is very
useful to handle paths conveniently and across platforms.
:::

## Dependencies

Most tasks have dependencies. Similar to products, you can use the
`@pytask.mark.depends_on` marker to attach a dependency to a task.

```python
@pytask.mark.depends_on(BLD / "data.pkl")
@pytask.mark.produces(BLD / "plot.png")
def task_plot_data(depends_on, produces):
    ...
```

Use `depends_on` as a function argument to work with the path of the dependency and, for
example, load the data.

:::{important}
The two markers, `pytask.mark.depends_on` and `pytask.mark.produces`, cannot be used
interchangeably! Use the first for dependencies and the latter for products.
:::

## Conversion

Dependencies and products do not have to be absolute paths. If paths are relative, they
are assumed to point to a location relative to the task module.

You can also use absolute and relative paths as strings which obey the same rules as the
{class}`pathlib.Path`.

```python
@pytask.mark.produces("../bld/data.pkl")
def task_create_random_data(produces):
    ...
```

If you use `depends_on` or `produces` as arguments for the task function, you will have
access to the paths of the targets as {class}`pathlib.Path` even if strings were used
before.

## Multiple dependencies and products

Most tasks have multiple dependencies or products. The easiest way to attach multiple
dependencies or products to a task is to pass a {class}`dict` (highly recommended),
{class}`list` or another iterator to the marker containing the paths.

To assign labels to dependencies or products, pass a dictionary. For example,

```python
@pytask.mark.produces({"first": BLD / "data_0.pkl", "second": BLD / "data_1.pkl"})
def task_create_random_data(produces):
    ...
```

Then, use

```pycon
>>> produces["first"]
BLD / "data_0.pkl"

>>> produces["second"]
BLD / "data_1.pkl"
```

inside the task function.

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

Why does pytask recommend dictionaries and even converts lists to dictionaries? First,
dictionaries with positions as keys behave very similar to lists and conversion between
both is easy.

:::{tip}
Use `list(produces.values())` to convert a dictionary to a list.
:::

Secondly, dictionaries use keys instead of positions which is more verbose and
descriptive and does not assume a fixed ordering. Both attributes are especially
desirable in complex projects.

## Multiple decorators

You can also attach multiple decorators to a function which will be merged into a single
dictionary. This might help you to group certain dependencies and apply them to multiple
tasks.

```python
common_dependencies = ["text_1.txt", "text_2.txt"]


@pytask.mark.depends_on(common_dependencies)
@pytask.mark.depends_on("text_3.txt")
def task_example():
    ...
```

## Nested dependencies and products

Dependencies and products are allowed to be nested containers consisting of tuples,
lists, and dictionaries. In situations where you want more structure and are otherwise
forced to flatten your inputs, this can be beneficial.

Here is an example with a task which fits some model on data. It depends on a module
containing the code for the model which is not actively used, but ensures that the task
is rerun when the model is changed. And, it depends on data.

```python
@pytask.mark.depends_on(
    {
        "model": [SRC / "models" / "model.py"],
        "data": {"a": SRC / "data" / "a.pkl", "b": SRC / "data" / "b.pkl"},
    }
)
@pytask.mark.produces(BLD / "models" / "fitted_model.pkl")
def task_fit_model():
    ...
```

It is also possible to merge nested containers. For example, you might want to reuse the
dependency on models for other tasks as well.

```python
model_dependencies = pytask.mark.depends_on({"model": [SRC / "models" / "model.py"]})


@model_dependencies
@pytask.mark.depends_on(
    {"data": {"a": SRC / "data" / "a.pkl", "b": SRC / "data" / "b.pkl"}}
)
@pytask.mark.produces(BLD / "models" / "fitted_model.pkl")
def task_fit_model():
    ...
```

In both cases, `depends_on` within the function will be

```python
{
    "model": [SRC / "models" / "model.py"],
    "data": {"a": SRC / "data" / "a.pkl", "b": SRC / "data" / "b.pkl"},
}
```

Tuples and lists are converted to dictionaries with integer keys. The innermost
decorator is evaluated first.

```python
@pytask.mark.depends_on([SRC / "models" / "model.py"])
@pytask.mark.depends_on([SRC / "data" / "a.pkl", SRC / "data" / "b.pkl"])
@pytask.mark.produces(BLD / "models" / "fitted_model.pkl")
def task_fit_model():
    ...
```

would give

```python
{0: SRC / "data" / "a.pkl", 1: SRC / "data" / "b.pkl", 2: SRC / "models" / "model.py"}
```

:::{seealso}
The general concept behind nested objects like tuples, lists, and dictionaries is called
pytrees and is more extensively explained in the [documentation of
pybaum](https://github.com/OpenSourceEconomics/pybaum) which serves pytask under the
hood.
:::

## References

[^id3]: The official documentation for {mod}`pathlib`.

[^id4]: A guide for pathlib by [realpython](https://realpython.com/python-pathlib/).
