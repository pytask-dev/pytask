# Write a task

Starting from the project structure in the {doc}`previous tutorial <set_up_a_project>`,
you will learn how to write your first task.

pytask will look for tasks in modules whose name starts with `task_`. Tasks are
functions in these modules whose name also begins with `task_`.

Our first task, `task_create_random_data`, will be defined in
`src/my_project/task_data_preparation.py`, and it will generate artificial data stored
in `bld/data.pkl`.

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

Let us define the task.

:::::{tab-set}

::::{tab-item} Python 3.10+

:::{tip}
pytask uses type hints in its interface. If you want to refresh your knowledge about
type hints, read [Type hints](../type_hints.md).
:::

```{literalinclude} ../../../docs_src/tutorials/write_a_task_py310.py
:emphasize-lines: 11
```

To let pytask track the product of the task, you need to use type hints with
{obj}`~typing.Annotated`. The first entry in {obj}`~typing.Annotated` defines the
type of the argument, a {class}`~pathlib.Path`, and the second argument adds metadata to
the argument. {class}`~pytask.Product` signals pytask that the argument is a product of
a task.

::::

::::{tab-item} Python 3.8+

:::{tip}
pytask uses type hints in its interface. If you want to refresh your knowledge about
type hints, read [Type hints](../type_hints.md).
:::

```{literalinclude} ../../../docs_src/tutorials/write_a_task_py38.py
:emphasize-lines: 11
```

To let pytask track the product of the task, you need to use type hints with
{obj}`~typing.Annotated`. The first entry in {obj}`~typing.Annotated` defines the
type of the argument, a {class}`~pathlib.Path`, and the second argument adds metadata to
the argument. {class}`~pytask.Product` signals pytask that the argument is a product of
a task.

::::

::::{tab-item} Decorators

```{warning}
This approach is deprecated and will be removed in v0.5
```

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
