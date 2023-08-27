# Write a task

Starting from the project structure in the {doc}`previous tutorial <set_up_a_project>`,
you will learn how to write your first task.

The task, `task_create_random_data`, will be defined in
`src/my_project/task_data_preparation.py`, and it will generate a data set stored
in `bld/data.pkl`.

The `task_` prefix for modules and task functions is important so that pytask
automatically discovers them.

```
my_project
├───pyproject.toml
│
├───src
│   └───my_project
│       ├────config.py
│       └────task_data_preparation.py
│
├───setup.py
│
├───.pytask.sqlite3
│
└───bld
    └────data.pkl
```

Generally, a task is a function whose name starts with `task_`. Tasks produce outputs
and the most common output is a file which we will focus on throughout the tutorials.

The following interfaces allow specifying the products of a task. It enables pytask to
peform some checks. For example, whether the file is created after the task was
executed. The interfaces are ordered from most (left) to least recommended (right).

:::::{tab-set}

::::{tab-item} Python 3.10+

The task accepts the argument `path` that points to the file where the data set will be
stored. The path is passed to the task via the default value, `BLD / "data.pkl"`. To
indicate that this file is a product we add some metadata to the argument.

Look at the type hint `Annotated[Path, BLD / "data.pkl"]`. It uses the new
{obj}`~typing.Annotated` syntax. The first entry is the type of the argument,
{class}`~pathlib.Path`. The second entry is {class}`pytask.Product` that marks this
argument as a product.

```{literalinclude} ../../../docs_src/tutorials/write_a_task_py310.py
:emphasize-lines: 3, 11
```

:::{tip}
If you want to refresh your knowledge about type hints, read
[this guide](../type_hints.md).
:::

::::

::::{tab-item} Python 3.8+

The task accepts the argument `path` that points to the file where the data set will be
stored. The path is passed to the task via the default value, `BLD / "data.pkl"`. To
indicate that this file is a product we add some metadata to the argument.

Look at the type hint `Annotated[Path, BLD / "data.pkl"]`. It uses the new
{obj}`~typing.Annotated` syntax. The first entry is the type of the argument,
{class}`~pathlib.Path`. The second entry is {class}`pytask.Product` that marks this
argument as a product.

```{literalinclude} ../../../docs_src/tutorials/write_a_task_py38.py
:emphasize-lines: 8, 11
```

:::{tip}
If you want to refresh your knowledge about type hints, read
[this guide](../type_hints.md).
:::

::::

::::{tab-item} &#8203;`produces`

Tasks can use `produces` as an argument name. Every value, or in this case path, passed
to this argument is automatically treated as a task product. Here, the path is given by
the default value of the argument.

```{literalinclude} ../../../docs_src/tutorials/write_a_task_produces.py
:emphasize-lines: 9
```

::::

::::{tab-item} Decorators

```{warning}
This approach is deprecated and will be removed in v0.5
```

To specify a product, pass the path to the
{func}`@pytask.mark.produces <pytask.mark.produces>` decorator. Then, add `produces` as
an argument name to use the path inside the task function.

```{literalinclude} ../../../docs_src/tutorials/write_a_task_decorators.py
:emphasize-lines: 10, 11
```

To let pytask track the product of the task, you need to use the
{func}`@pytask.mark.produces <pytask.mark.produces>` decorator.

::::
:::::

Now, execute pytask to collect tasks in the current and subsequent directories.

```{include} ../_static/md/write-a-task.md
```

## Customize task names

Use the {func}`@pytask.mark.task <pytask.mark.task>` decorator to mark a function as a
task regardless of its function name. You can optionally pass a new name for the task.
Otherwise, pytask uses the function name.

```python
# The id will be ".../task_data_preparation.py::create_random_data".


@pytask.mark.task
def create_random_data():
    ...


# The id will be ".../task_data_preparation.py::create_data".


@pytask.mark.task(name="create_data")
def create_random_data():
    ...
```

## Customize task module names

Use the configuration value {confval}`task_files` if you prefer a different naming
scheme for the task modules. `task_*.py` is the default. You can specify one or multiple
patterns to collect tasks from other files.
