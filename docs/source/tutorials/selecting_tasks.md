# Selecting tasks

Multiple options exist if you want to run a subset of tasks.

(markers)=

## Markers

You can use marker expressions to select tasks if you assign markers to task functions.
For example, here is a task with the `wip` marker, which indicates work-in-progress.

```python
@pytask.mark.wip
def task_1():
    pass
```

Run this command in your terminal to execute only tasks with the `wip` marker.

```console
$ pytask -m wip
```

You can pass more complex expressions to {option}`pytask build -m` by using multiple
markers and `and`, `or`, `not`, and `()`. The following pattern selects all tasks that
belong to the data management but not those that produce plots and plots for the
analysis.

```console
$ pytask -m "(data_management and not plots) or (analysis and plots)"
```

If you create your markers, use {confval}`markers` to register and document them.

(expressions)=

## Expressions

Expressions are similar to markers and offer the same syntax but target the task ids
with {option}`pytask build -k`. Assume you have the following tasks.

```python
def task_1():
    pass


def task_2():
    pass


def task_12():
    pass
```

Then, the following command will run the first and third tasks.

```console
$ pytask -k 1
```

The following command will only execute the first task.

```console
$ pytask -k "1 and not 2"
```

This command only runs the first two tasks.

```console
$ pytask -k "1 or 2 and not 12"
```

To execute a single task, say `task_run_this_one` in `task_example.py`, use

```console
$ pytask -k task_example.py::task_run_this_one

# or

$ pytask -k task_run_this_one
```

### Selecting repeated tasks

If you have a parametrized task, you can select individual parametrizations.

```python
from pytask import task


for i in range(2):

    @task
    def task_parametrized(i=i):
        ...
```

To run the task where `i = 1`, run this command.

```console
$ pytask -k "task_parametrized[1]"
```

pytask uses booleans, floats, integers, and strings in the task id. It replaces other
Python objects like tuples with a combination of the argument name and an iteration
counter and separates multiple arguments via dashes.

```{seealso}
Read this {ref}`section <how-to-repeat-a-task-with-different-inputs-the-id>` for more
information on how ids for repeated tasks are created and can be customized.
```
