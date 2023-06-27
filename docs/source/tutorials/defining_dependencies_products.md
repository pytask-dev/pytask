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

```python
@pytask.mark.produces(BLD / "data.pkl")
def task_create_random_data(produces):
    ...
```

The {func}`@pytask.mark.produces <pytask.mark.produces>` marker attaches a product to a
task which is a {class}`pathlib.Path` to file. After the task has finished, pytask will
check whether the file exists.

Add `produces` as an argument of the task function to get access to the same path inside
the task function.

:::{tip}
If you do not know about {mod}`pathlib` check out [^id3] and [^id4]. The module is
beneficial for handling paths conveniently and across platforms.
:::

## Dependencies

Most tasks have dependencies. Like products, you can use the
{func}`@pytask.mark.depends_on <pytask.mark.depends_on>` marker to attach a
dependency to a task.

```python
@pytask.mark.depends_on(BLD / "data.pkl")
@pytask.mark.produces(BLD / "plot.png")
def task_plot_data(depends_on, produces):
    df = pd.read_pickle(depends_on)
    ...
```

Add `depends_on` as a function argument to work with the path of the dependency and, for
example, load the data.

## Conversion

Dependencies and products do not have to be absolute paths. If paths are relative, they
are assumed to point to a location relative to the task module.

You can also use absolute and relative paths as strings that obey the same rules as the
{class}`pathlib.Path`.

```python
@pytask.mark.produces("../bld/data.pkl")
def task_create_random_data(produces):
    ...
```

## Multiple dependencies and products

The easiest way to attach multiple dependencies or products to a task is to pass a
{class}`dict` (highly recommended), {class}`list`, or another iterator to the marker
containing the paths.

To assign labels to dependencies or products, pass a dictionary. For example,

```python
@pytask.mark.produces({"first": BLD / "data_0.pkl", "second": BLD / "data_1.pkl"})
def task_create_random_data(produces):
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

## References

[^id3]: The official documentation for {mod}`pathlib`.

[^id4]: A guide for pathlib by [realpython](https://realpython.com/python-pathlib/).
