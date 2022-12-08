# How to influence the build order

:::{important}
This guide shows how to influence the order in which tasks are executed. The feature
should be treated with caution since it might make projects work whose dependencies and
products are not fully specified.
:::

You can influence the order in which tasks are executed by assigning preferences to
tasks. Use {func}`@pytask.mark.try_first <pytask.mark.try_first>` to execute a task as
early as possible and {func}`@pytask.mark.try_last <pytask.mark.try_last>` to defer
execution.

:::{note}
A little bit more background: Tasks, dependencies and products form a directed acyclic
graph (DAG). A [topological ordering](https://en.wikipedia.org/wiki/Topological_sorting)
determines the order in which tasks are executed such that tasks are not run until their
predecessors have been executed. You should not assume a fixed ordering in which tasks
are executed.
:::

As an example, here are two tasks where the decorator ensures that the output of the
second task is always shown before the output of the first task.

```python
# Content of task_example.py

import pytask


def task_first():
    print("I'm second.")


@pytask.mark.try_first
def task_second():
    print("I'm first.")
```

The execution yields (use `-s` to make the output visible in the terminal)

```{include} ../_static/md/try-first.md
```

Replacing {func}`pytask.mark.try_first` with {func}`pytask.mark.try_last` yields

```python
# Content of task_example.py

import pytask


def task_first():
    print("I'm second.")


@pytask.mark.try_last
def task_second():
    print("I'm first.")
```

and

```{include} ../_static/md/try-last.md
```
