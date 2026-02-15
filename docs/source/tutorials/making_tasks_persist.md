# Making tasks persist

Sometimes you want to skip the execution of a task and pretend nothing has changed.

A typical scenario is that you formatted the task's source files with
[black](https://github.com/psf/black) which would rerun the task.

In this case, you can apply the `@pytask.mark.persist` decorator to the task, which will
skip its execution as long as all products exist.

Internally, the state of the dependencies, the source file, and the products are updated
in the database such that the subsequent execution will skip the task successfully.

## When is this useful?

- You ran a formatter like ruff on the files in your project and want to prevent the
    longest-running tasks from being rerun.
- You extend a repetition of a task function but do not want to rerun all tasks.
- You want to integrate a task that you have already run elsewhere. Copy over the
    dependencies and products and the task definition and make the task persist.

!!! caution

    This feature can corrupt the integrity of your project. Document why you have applied
    the decorator out of consideration for yourself and other contributors.

## How to do it?

To create a persisting task, apply the correct decorator, and, et voilà, it is done.

First, we create a task and its dependency.

```py
--8<-- "docs_src/tutorials/making_tasks_persist.py"
```

```md
<!-- Content of input.md. -->

Here is the text.
```

Running pytask will execute the task since the product is missing.

--8<-- "docs/source/_static/md/persist-executed.md"

After that, we accidentally changed the task's source file by formatting the file with
Black. Without the `@pytask.mark.persist` decorator, the task would run again since the
source has changed. With the decorator, a green p signals that the execution is skipped.

--8<-- "docs/source/_static/md/persist-persisted.md"

If we rerun the task, it is skipped because nothing has changed and not because it is
marked with `@pytask.mark.persist`.

--8<-- "docs/source/_static/md/persist-skipped.md"
