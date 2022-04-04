# Write a task

Starting from the project structure in the
{doc}`previous tutorial <set_up_a_project>`, this tutorial teaches you how to
write your first task.

By default, pytask will look for tasks in modules whose name is prefixed with `task_`.
Tasks are functions in these modules whose name also starts with `task_`.

Our first task will be defined in `src/my_project/task_data_preparation.py` and it will
generate artificial data which will be stored in `bld/data.pkl`. We will call the
function in the module {func}`task_create_random_data`.

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

Here, we define the function

```python
# Content of task_data_preparation.py.

import pytask
import numpy as np
import pandas as pd

from my_project.config import BLD


@pytask.mark.produces(BLD / "data.pkl")
def task_create_random_data(produces):
    rng = np.random.default_rng(0)
    beta = 2

    x = rng.normal(loc=5, scale=10, size=1_000)
    epsilon = rng.standard_normal(1_000)

    y = beta * x + epsilon

    df = pd.DataFrame({"x": x, "y": y})
    df.to_pickle(produces)
```

To let pytask track the product of the task, you need to use the
{func}`@pytask.mark.produces <_pytask.collect_utils.produces>` decorator.

:::{seealso}
You learn more about adding dependencies and products to a task in the next
{doc}`tutorial <defining_dependencies_products>`.
:::

Now, execute pytask which will automatically collect tasks in the current directory and
subsequent directories.

```{image} /_static/images/write-a-task.svg
```

## Customize task names

Use the {func}`@pytask.mark.task <_pytask.task_utils.task>` decorator to mark a function
as a task regardless of its function name. You can optionally pass a new name for the
task. Otherwise, the function name is used.

```python
# The id will be '.../task_data_preparation.py::create_random_data'


@pytask.mark.task
def create_random_data():
    ...


# The id will be '.../task_data_preparation.py::create_data'


@pytask.mark.task(name="create_data")
def create_random_data():
    ...
```

## Customize task module names

Use the configuration value {confval}`task_files` if you prefer a different naming
scheme for the task modules. By default, it is set to `task_*.py`. You can specify one
or multiple patterns to collect tasks from other files.
