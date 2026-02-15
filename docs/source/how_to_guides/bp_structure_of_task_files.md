# Structure of task files

This guide presents some best-practices for structuring your task files. You do not have
to follow them to use pytask or to create a reproducible research project. But, if you
are looking for orientation or inspiration, here are some tips.

## TL;DR

- Use task modules to separate task functions from another. Separating tasks by the
    stages in research project like data management, analysis, plotting is a good start.
    Separate further when task modules become crowded.
- Task functions should be at the top of a task module to easily identify what the
    module is for.
- The purpose of the task function is to handle IO operations like loading and saving
    files and calling Python functions on the task's inputs. IO should not be handled in
    any other function.
- Non-task functions in the task module are
    [`private functions`](../glossary.md#private-function) and only used within this
    task module. The functions should not have side-effects.
- It should never be necessary to import from task modules. So if you need a function in
    multiple task modules, put it in a separate module (which does not start with
    `task_`).

!!! note

    The only exception might be for [repetitions](bp_complex_task_repetitions.md).

## Best Practices

### Number of tasks in a module

There are two reasons to split tasks across several modules.

The first reason concerns readability and complexity. Tasks deal with different concepts
and, thus, should be split. Even if tasks deal with the same concept, they might become
very complex and separate modules help the reader (most likely you or your colleagues)
to focus on one thing.

The second reason is about runtime. If a task module is changed, all tasks within the
module are re-run. If the runtime of all tasks in the module is high, you wait longer
for your tasks to finish or until an error occurs which prolongs your feedback loops and
hurts your productivity. Use [`@pytask.mark.persist`](../api/marks.md#pytaskmarkpersist)
if you want to avoid accidentally triggering an expensive task. It is also explained in
[this tutorial](../tutorials/making_tasks_persist.md).

### Structure of the module

For the following example, let us assume that the task module contains one task.

The task function should be the first function in the module. It should have a
descriptive name and a docstring which explains what the task accomplishes.

It should be the only [`public function`](../glossary.md#public-function) in the module
which means the only function without a leading underscore. This is a convention to keep
[`public functions`](../glossary.md#public-function) separate from
[`private functions`](../glossary.md#private-function) (with a leading underscore) where
the latter must only be used in the same module and not imported elsewhere.

The body of the task function should contain two things:

1. Any IO operations like reading and writing files which are necessary for this task.

    The reason is that IO operations introduce side-effects since the result of the
    function does not only depend on the function arguments, but also on the IO
    resource (e.g., a file on the disk).

    If we bundle all IO operations in the task functions, all other functions used in
    task remain pure (without side-effects) which makes testing the functions easier.

1. The task function should either call `private functions` defined inside the task
    module or functions which are shared between tasks and defined in a module
    separated from all tasks.

The rest of the module is made of `private functions` with a leading underscore which
are used to accomplish this and only this task.

Here is an example of a task module which conforms to all advice.

```python
--8 < --"docs_src/how_to_guides/bp_structure_of_task_files.py"
```

!!! note

    The structure of the task module is greatly inspired by John Ousterhout's "A Philosophy
    of Software Design" in which he coins the name "deep modules". In short, deep modules
    have simple interfaces which are defined by one or a few `public functions` (or classes)
    which provide the functionality. The complexity is hidden inside the module in
    `private functions` which are called by the `public functions`.
