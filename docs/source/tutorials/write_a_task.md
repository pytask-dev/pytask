# Write a task

Using the project structure from the [previous tutorial](set_up_a_project.md), write
your first task.

The task `task_create_random_data` is defined in
`src/my_project/task_data_preparation.py` and generates a data set stored in
`bld/data.pkl`.

The `task_` prefix for modules and task functions is important so that pytask
automatically discovers them.

```text
my_project
│
├───.pytask
│
├───bld
│   └────data.pkl
│
├───src
│   └───my_project
│       ├────__init__.py
│       ├────config.py
│       └────task_data_preparation.py
│
└───pyproject.toml
```

Generally, a task is a function whose name starts with `task_`. Tasks produce outputs
and the most common output is a file which we will focus on throughout the tutorials.

The following interfaces are different ways to specify the products of a task which is
necessary for pytask to correctly run a workflow. The interfaces are ordered from most
(left) to least recommended (right).

!!! important

```
You cannot mix different interfaces for the same task. Choose only one.
```

=== "Annotated"

````
The task accepts the argument `path` that points to the file where the data set will be
stored. The path is passed to the task via the default value, `BLD / "data.pkl"`. To
indicate that this file is a product we add some metadata to the argument.

The type hint `Annotated[Path, Product]` uses
`typing.Annotated` syntax. The first entry specifies the argument type
(`pathlib.Path`), and the second entry (`pytask.Product`) marks this
argument as a product.

``` { .python .annotate hl_lines="3 13" }
--8<-- "docs_src/tutorials/write_a_task_py310.py"
```

1. This example lives in `task_data_preparation.py`.
2. `Annotated[Path, Product]` marks the argument as a task product.

!!! tip

    If you want to refresh your knowledge about type hints, read
    [this guide](../type_hints.md).
````

=== "produces"

````
Tasks can use `produces` as an argument name. Every value, or in this case path, passed
to this argument is automatically treated as a task product. Here, the path is given by
the default value of the argument.

``` { .python .annotate hl_lines="9" }
--8<-- "docs_src/tutorials/write_a_task_produces.py"
```

1. This example lives in `task_data_preparation.py`.
2. Using the argument name `produces` marks this path as a task product.
````

Now, execute pytask to collect tasks in the current and subsequent directories.

--8<-- "docs/source/_static/md/write-a-task.md"

<a id="customize-task-names"></a>

## Customize task names

Use the `@task` decorator to mark a function as a task regardless of its function name.
You can optionally pass a new name for the task. Otherwise, pytask uses the function
name.

```python
from pytask import task

# The id will be ".../task_data_preparation.py::create_random_data".


@task
def create_random_data(): ...


# The id will be ".../task_data_preparation.py::create_data".


@task(name="create_data")
def create_random_data(): ...
```

## Customize task module names

Use the configuration value `task_files` if you prefer a different naming scheme for the
task modules. `task_*.py` is the default. You can specify one or multiple patterns to
collect tasks from other files.
