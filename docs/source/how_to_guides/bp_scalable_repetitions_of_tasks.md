# Scalable repetitions of tasks

This section advises on how to use repetitions to scale your project quickly.

## TL;DR

- Loop over dictionaries that map ids to `kwargs` to create multiple tasks.
- Create the dictionary with a separate function.
- Create functions to build intermediate objects like output paths which can be shared
  more easily across tasks than the generated values.

## Scalability

Parametrizations allow scaling tasks from $1$ to $N$ in a simple way. What is easily
overlooked is that parametrizations usually trigger other parametrizations and the
growth in tasks is more $1$ to $N \cdot M \cdot \dots$ or $1$ to $N^{M \cdot \dots}$.

This guide lays out a simple, modular, and scalable structure to fight complexity.

For example, assume we have four datasets with one binary dependent variable and some
independent variables. We fit three models on each data set: a linear model, a logistic
model, and a decision tree. In total, we have $4 \cdot 3 = 12$ tasks.

First, let us look at the folder and file structure of such a project.

```
my_project
├───pyproject.toml
│
├───src
│   └───my_project
│       ├────config.py
│       │
│       ├───data
│       │   ├────data_0.csv
│       │   ├────data_1.csv
│       │   ├────data_2.csv
│       │   └────data_3.csv
│       │
│       ├───data_preparation
│       │   ├────__init__.py
│       │   ├────config.py
│       │   └────task_prepare_data.py
│       │
│       └───estimation
│           ├────__init__.py
│           ├────config.py
│           └────task_estimate_models.py
│
│
├───setup.py
│
├───.pytask.sqlite3
│
└───bld
```

The folder structure, the main `config.py` which holds `SRC` and `BLD`, and the tasks
follow the same structure advocated throughout the tutorials.

What is new are the local configuration files in each subfolder of `my_project`, which
contain objects shared across tasks. For example, `config.py` holds the paths to the
processed data and the names of the data sets.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scalable_repetitions_of_tasks_1.py
```

The task file `task_prepare_data.py` uses these objects to build the parametrization.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scalable_repetitions_of_tasks_2.py
```

All arguments for the loop and the {func}`@task <pytask.task>` decorator is built within
a function to keep the logic in one place and the module's namespace clean.

Ids are used to make the task {ref}`ids <ids>` more descriptive and to simplify their
selection with {ref}`expressions <expressions>`. Here is an example of the task ids with
an explicit id.

```
# With id
.../my_project/data_preparation/task_prepare_data.py::task_prepare_data[data_0]
```

Next, we move to the estimation to see how we can build another parametrization upon the
previous one.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scalable_repetitions_of_tasks_3.py
```

In the local configuration, we define `ESTIMATIONS` which combines the information on
data and model. The dictionary's key can be used as a task id whenever the estimation is
involved. It allows triggering all tasks related to one estimation - estimation,
figures, tables - with one command.

```console
pytask -k linear_probability_data_0
```

And here is the task file.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scalable_repetitions_of_tasks_4.py
```

Replicating this pattern across a project allows a clean way to define parametrizations.

## Extending parametrizations

Some parametrized tasks are costly to run - costly in terms of computing power, memory,
or time. Users often extend parametrizations triggering all parametrizations to be
rerun. Thus, use the {func}`@pytask.mark.persist <pytask.mark.persist>` decorator, which
is explained in more detail in this {doc}`tutorial <../tutorials/making_tasks_persist>`.
