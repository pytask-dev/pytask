# Scaling tasks

- \[ \] Write about adding another dimension.
- \[ \] Write about adding another level.
- \[ \] Write about executing subsets of tasks.
- \[ \] Write about grouping by one dimension´or aggregating.

In projects where task inputs and outputs are sufficiently standardized, it is possible
to make extensive use of task repetition.

A common pattern is to write multiple loops around a task function where each loop
stands for a different dimension. A dimension, for example, represents different
datasets or model specifications to analyze the datasets.

There is nothing wrong with using nested loops for simpler projects that are clearly
defined in scope. But, often they are just the start of looking at a problem from
different angles and soon you want to add more dimensions.

Adding another loop in a lot of places in your project is cumbersome and the increased
indentation is visually displeasing.

It is not the most serious problem, though. More importantly, it becomes cumbersome to
reference dependencies of products and to set unique identifiers for tasks. The latter
is important to execute only subsets of the project.

How do we solve these problems? Here is a brief explanation of the solution.

1. Create objects to define every dimension in the project. A dimension can be
   characterized by a single value like a {class}`~pathlib.Path`, an
   {class}`~enum.Enum`, or a {class}`~typing.NamedTuple` or
   {func}`~dataclasses.dataclass` if more fields are needed.

1. Create an object like a {class}`~typing.NamedTuple` or a
   {func}`~dataclasses.dataclass` that has one attribute for each dimension. For lack of
   a better name, we will call this unit an experiment.

   The experiment combines the information provided by each dimension to create a unique
   identifier for each experiment and the names or paths of dependencies and products
   for each task.

To make the idea more tangible, let us focus on an example.

## Example

Let us assume we have a project with multiple datasets and model specifications that
should be fitted to the data.

The datasets are created by the task from the
{doc}`tutorials <../tutorials/defining_dependencies_products>` parametrized with
different coefficients.

Below that is the task that fits different models to the datasets using a double loop.

```python
from pathlib import Path
from pytask import task, Product


SRC = Path(__file__).parent
BLD = SRC / "bld"





for dat



for data_name in ("a", "b", "c"):
    for model_name in ("ols", "logit", "linear_prob"):

        @task
        def task_fit_model(path_to_data: Path = SRC / f"{data_name}.pkl")

```

1. The level of indentation is not visually pleasing and does not allow us to
   sufficiently use every line in the file.

1. Whenever we add another dimension to our problem, we need to extend every occurrence
   of the nested loops.

But, these problems are more annoying than truly

The first and most important problem is that

The first problem is t

There are couple of problems that arise in these projects.

The main problem is that with

In projects where task inputs and outputs can be standardized and general interface

In many projects, tasks are repeated across multiple dimensions that are stacked on top
of each other.

For example, take a project that there are four ways to simulate data and there are
three different models that should be fitted on each dataset.

Assuming there is a high-level interface to simulate data, we can loop over the task for
simulating data four times with different arguments.

Assuming there is a high-level interface to fit models to data,

Assuming that you can easily switch the model the model fitting can be done in a taskThe
cartesian product of all steps combined comprises twelve differently fitted models.

This guide shows an approach to organizing your tasks that can be best described as
flattening the loops.

## The data catalog

First of all, we need to create a data catalog in a `config.py` in your project.

The data catalog plays a key role in managing lots of repetitions of tasks because it

## Scalability

Let us dive right into the aforementioned example. We start with one dataset `data.csv`.
Then, we will create four different specifications of the data and, finally, fit three
different models to each specification.

This is the structure of the project.

```text
my_project
├───pyproject.toml
│
├───src
│   └───my_project
│       ├────config.py
│       │
│       ├───data
│       │   └────data.csv
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
├───.pytask
│   └────...
│
└───bld
```

The folder structure, the main `config.py` which holds `SRC` and `BLD`, and the tasks
follow the same structure advocated throughout the tutorials.

New are the local configuration files in each subfolder of `my_project`, which contain
objects shared across tasks. For example, `config.py` holds the paths to the processed
data and the names of the data sets.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scaling_tasks_1.py
```

The task file `task_prepare_data.py` uses these objects to build the repetitions.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scaling_tasks_2.py
```

All arguments for the loop and the {func}`@task <pytask.task>` decorator are built
within a function to keep the logic in one place and the module's namespace clean.

Ids are used to make the task {ref}`ids <ids>` more descriptive and to simplify their
selection with {ref}`expressions <expressions>`. Here is an example of the task ids with
an explicit id.

```
# With id
.../my_project/data_preparation/task_prepare_data.py::task_prepare_data[data_0]
```

Next, we move to the estimation to see how we can build another repetition on top.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scaling_tasks_3.py
```

In the local configuration, we define `ESTIMATIONS` which combines the information on
data and model. The dictionary's key can be used as a task id whenever the estimation is
involved. It allows triggering all tasks related to one estimation - estimation,
figures, tables - with one command.

```console
pytask -k linear_probability_data_0
```

And here is the task file.

```{literalinclude} ../../../docs_src/how_to_guides/bp_scaling_tasks_4.py
```

Replicating this pattern across a project allows a clean way to define repetitions.

## Extending repetitions

Some parametrized tasks are costly to run - costly in terms of computing power, memory,
or time. Users often extend repetitions triggering all repetitions to be rerun. Thus,
use the {func}`@pytask.mark.persist <pytask.mark.persist>` decorator, which is explained
in more detail in this {doc}`tutorial <../tutorials/making_tasks_persist>`.
