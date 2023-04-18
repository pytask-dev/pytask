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

Here, we define the function.

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
{func}`@pytask.mark.produces <pytask.mark.produces>` decorator.

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
