# How to select tasks

If you want to run only a subset of tasks, there exist multiple options.

## Paths

You can run all tasks in one file or one directory by passing the corresponding path to
pytask. The same can be done for multiple paths.

```console
$ pytask src/task_1.py

$ pytask src

$ pytask src/task_1.py src/task_2.py
```

(markers)=

## Markers

If you assign markers to task functions, you can use marker expressions to select tasks.
For example, here is a task with the `wip` marker which indicates work-in-progress.

```python
@pytask.mark.wip
def task_1():
    pass
```

To execute only tasks with the `wip` marker, use

```console
$ pytask -m wip
```

You can pass more complex expressions to `-m` by using multiple markers and `and`, `or`,
`not`, and `()`. The following pattern selects all tasks which belong to the data
management, but not the ones which produce plots and plots produced for the analysis.

```console
$ pytask -m "(data_management and not plots) or (analysis and plots)"
```

(expressions)=

## Expressions

### General

Expressions are similar to markers and offer the same syntax but target the task ids.
Assume you have the following tasks.

```python
def task_1():
    pass


def task_2():
    pass


def task_12():
    pass
```

Then,

```console
$ pytask -k 1
```

will execute the first and third task and

```console
$ pytask -k "1 and not 2"
```

executes only the first task.

To execute a single task, say `task_run_this_one` in `task_example.py`, use

```console
$ pytask -k task_example.py::task_run_this_one
```

(how-to-select-tasks-parametrization)=

### Parametrization

If you have a parametrized task, you can select individual parametrizations.

```python
@pytask.mark.parametrize("i", range(2))
def task_parametrized(i):
    pass
```

To run the task where `i = 1`, type

```console
$ pytask -k task_parametrized[1]
```

Booleans, floats, integers, and strings are used in the task id as they are, but all
other Python objects like tuples are replaced with a combination of the argument name
and an iteration counter. Multiple arguments are separated via dashes.

:::{seealso}
See this {ref}`section <how_to_parametrize_a_task_the_id>` for more information how ids
for parametrized tasks are generated.
:::
