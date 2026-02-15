# Skipping tasks

Skipping tasks is one way to prevent tasks from being executed. It is more persistent
but less dynamic than selecting tasks via [markers](selecting_tasks.md#markers) or
[expressions](selecting_tasks.md#expressions).

In contrast to tasks in ignored files, ignored with `ignore`, pytask will still check
whether skipped tasks are consistent with the [DAG](../glossary.md#dag) of the project.

For example, you can use the [`@pytask.mark.skip`](../api/marks.md#pytask.mark)
decorator to skip tasks during development that take too much time to compute right now.

```py
--8<-- "docs_src/tutorials/skipping_tasks_example_1.py"
```

Not only will this task be skipped, but all tasks depending on
`time_intensive_product.pkl`.

## Conditional skipping

In large projects, you may have many long-running tasks that you only want to execute on
a remote server, but not when you are not working locally.

In this case, use the [`@pytask.mark.skipif`](../api/marks.md#pytask.mark) decorator,
which requires a condition and a reason as arguments.

Place the condition variable in a module different from the task so you can change it
without causing a rerun of the task.

```py title="config.py"
NO_LONG_RUNNING_TASKS = True
```

```py title="task_long_running.py"
from pathlib import Path

import pytask
from config import NO_LONG_RUNNING_TASKS


@pytask.mark.skipif(NO_LONG_RUNNING_TASKS, reason="Skip long-running tasks.")
def task_that_takes_really_long_to_run(
    path: Path = Path("time_intensive_product.pkl"),
): ...
```

## Further reading

- [selecting tasks](selecting_tasks.md).
- [`ignore`](../reference_guides/configuration.md#ignore) on how to ignore task files.
