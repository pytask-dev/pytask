# Skipping tasks

Skipping tasks is one way to prevent tasks from being executed. It is more persistent
but less dynamic than selecting tasks via {ref}`markers <markers>` or
{ref}`expressions <expressions>`.

In contrast to tasks in ignored files, ignored with {confval}`ignore`, pytask will still
check whether skipped tasks are consistent with the DAG of the project.

For example, you can use the {func}`@pytask.mark.skip <pytask.mark.skip>` decorator to
skip tasks during development which take too much time to compute right now.

```python
# Content of task_create_dependency.py


@pytask.mark.skip
@pytask.mark.produces("time_intensive_product.pkl")
def task_long_running(produces):
    ...
```

Not only this task will be skipped, but also all tasks which depend on
`time_intensive_product.pkl`.

## Conditional skipping

In large projects, you may have many long running tasks that you only want to execute on
a remote server but not when you are not working locally.

In this case, use the {func}`@pytask.mark.skipif <pytask.mark.skipif>` decorator which
requires a condition and a reason as arguments:

```python
# Content of a config.py

NO_LONG_RUNNING_TASKS = True
```

```python
# Content of task_create_dependency.py


@pytask.mark.produces("run_always.md")
def task_always(produces):
    ...
```

```python
# Content of task_long_running.py

from config import NO_LONG_RUNNING_TASKS


@pytask.mark.skipif(NO_LONG_RUNNING_TASKS, reason="Skip long-running tasks.")
@pytask.mark.depends_on("time_intensive_product.pkl")
def task_that_takes_really_long_to_run(depends_on):
    ...
```

## Further Reading

- {doc}`selecting_tasks`.
- {confval}`ignore` on how to ignore task files.
