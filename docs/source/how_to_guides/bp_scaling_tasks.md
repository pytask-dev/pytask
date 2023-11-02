# Scaling tasks

In any bigger project you quickly come to the point where you stack multiple repetitions
of tasks on top of each other.

For example, you have one dataset, four different ways to prepare it, and three
statistical models to analyze the data. The cartesian product of all steps combined
comprises twelve differently fitted models.

Here you find some tips on how to set up your tasks such that you can easily modify the
cartesian product of steps.

## Scalability

Let us dive right into the aforementioned example. We start with one dataset `data.csv`.
Then, we will create four different specifications of the data and, finally, fit three
different models to each specification.

This is the structure of the project.

```
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
│
├───setup.py
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
