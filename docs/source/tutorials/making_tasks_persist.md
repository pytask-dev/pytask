# Making tasks persist

Sometimes you want to skip the execution of a task and pretend as nothing has changed.

A typical scenario is that you formatted the task's source files with [black](https://github.com/psf/black) which would rerun the task.

In this case, you can apply the {func}`@pytask.mark.persist <pytask.mark.persist>`
decorator to the task, which will skip its execution as long as all products exist.

Internally, the state of the dependencies, the source file, and the products are updated
in the database such that the subsequent execution will skip the task successfully.

## When is this useful?

- You ran a formatter like Black on the files in your project and want to prevent the
  longest-running tasks from being rerun.
- You extend a repetition of a task function but do not want to rerun all tasks.
- You want to integrate a task that you have already run elsewhere. Copy over the
  dependencies and products and the task definition and make the task persist.

:::{caution}
This feature can corrupt the integrity of your project. Document why you have applied
the decorator out of consideration for yourself and other contributors.
:::

## How to do it?

To create a persisting task, apply the correct decorator, and, et voilà, it is done.

First, to see the whole process, we create a task and its dependency.

```python
# Content of task_module.py

import pytask


@pytask.mark.persist
@pytask.mark.depends_on("input.md")
@pytask.mark.produces("output.md")
def task_make_input_bold(depends_on, produces):
    produces.write_text("**" + depends_on.read_text() + "**")
```

```md
<!-- Content of input.md. -->

Here is the text.
```

Running pytask will execute the task since the product is missing.

```{image} /_static/images/persist-executed.svg
```

After that, we accidentally changed the task's source file by formatting the file
with Black. Without the {func}`@pytask.mark.persist <pytask.mark.persist>` decorator the
task would run again since it has changed. With the decorator, the execution is skipped
which is signaled by a green p.

```{image} /_static/images/persist-persisted.svg
```

If we rerun the task, it is skipped because nothing has changed and not because
it is marked with {func}`@pytask.mark.persist <pytask.mark.persist>`.

```{image} /_static/images/persist-skipped.svg
```
