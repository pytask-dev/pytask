# Delayed tasks

pytask's execution model can usually be separated into three phases.

1. Collection of tasks, dependencies, and products.
1. Building the DAG.
1. Executing the tasks.

But, in some situations pytask needs to be more flexible.

Imagine you want to download files from an online storage, but the total number of files
and their filenames is unknown before the task has started. How can you describe the
files still as products of the task?

And how would you define a task that depends on these files. Or, how would define a
single task to process each file.

The following sections will explain how delayed tasks work with pytask.

## Delayed Products

Let us start with a task that downloads an unknown amount of files and stores them on
disk in a folder called `downloads`. As an example, we will download all files without a
file extension from the pytask repository.

```{literalinclude} ../../../docs_src/how_to_guides/delayed_tasks_delayed_products.py
---
emphasize-lines: 4, 11
---
```

Since the names of the filesare not known when pytask is started, we need to use a
{class}`~pytask.DelayedPathNode`. With a {class}`~pytask.DelayedPathNode` we can specify
where pytask can find the files and how they look like with an optional path and a glob
pattern.

When we use the {class}`~pytask.DelayedPathNode` as a product annotation, we get access
to the `root_dir` as a {class}`~pathlib.Path` object inside the function which allows us
to store the files.

## Delayed task

In the next step, we want to define a task that consumes all previously downloaded files
and merges them into one file.

```{literalinclude} ../../../docs_src/how_to_guides/delayed_tasks_delayed_task.py
---
emphasize-lines: 8-10
---
```

When {class}`~pytask.DelayedPathNode` is used as a dependency a list of all the files in
the folder defined by the root path and the pattern are automatically collected and
passed to the task.

As long as we use a {class}`DelayedPathNode` with the same `root_dir` and `pattern` in
both tasks, pytask will automatically recognize that the second task depends on the
first. If that is not true, you might need to make this dependency more explicit by
using {func}`@task(after=...) <pytask.task>` which is explained {ref}`here <after>`.

## Delayed and repeated tasks

Coming to the last use-case, what if we wanted to process each of the downloaded files
separately instead of dealing with them in one task?

To define an unknown amount of tasks for an unknown amount of downloaded files, we have
to write a task generator.

A task generator is a task function in which we define more tasks, just as if we were
writing functions in a normal task module.

As an example, each task takes one of the downloaded files and copies its content to a
`.txt` file.

```{literalinclude} ../../../docs_src/how_to_guides/delayed_tasks_task_generator.py
```
