# Provisional nodes and task generators

pytask's execution model can usually be separated into three phases.

1. Collection of tasks, dependencies, and products.
1. Building the DAG.
1. Executing the tasks.

But, in some situations, pytask needs to be more flexible.

Imagine you want to download files from an online storage, but the total number of files
and their filenames is unknown before the task has started. How can you still describe
the files as products of the task?

And how would you define a task that depends on these files. Or, how would define a
single task to process each file.

The following sections will explain how you use pytask in these situations.

## Producing provisional nodes

Let us start with a task that downloads an unknown amount of files and stores them on
disk in a folder called `downloads`. As an example, we will download all files from the
pytask repository without a file extension.

```{literalinclude} ../../../docs_src/how_to_guides/delayed_tasks_delayed_products.py
---
emphasize-lines: 4, 11
---
```

Since the names of the files are not known when pytask is started, we need to use a
{class}`~pytask.DirectoryNode`. With a {class}`~pytask.DirectoryNode` we can specify
where pytask can find the files. The files are described with a path (default is the
directory of the task module) and a glob pattern (default is `*`).

When we use the {class}`~pytask.DirectoryNode` as a product annotation, we get access to
the `root_dir` as a {class}`~pathlib.Path` object inside the function, which allows us
to store the files.

```{note}
The {class}`~pytask.DirectoryNode` is a provisional node that implements
{class}`~pytask.PProvisionalNode`. A provisional node is not a {class}`~pytask.PNode`,
but when its {meth}`~pytask.PProvisionalNode.collect` method is called, it returns
actual nodes. A {class}`~pytask.DirectoryNode`, for example, returns
{class}`~pytask.PathNode`.
```

## Depending on provisional nodes

In the next step, we want to define a task that consumes and merges all previously
downloaded files into one file.

```{literalinclude} ../../../docs_src/how_to_guides/delayed_tasks_delayed_task.py
---
emphasize-lines: 9
---
```

Here, we use a {class}`~pytask.DirectoryNode` as a dependency since we do not know the
names of the downloaded files. Before the task is executed, the list of files in the
folder defined by the root path and the pattern are automatically collected and passed
to the task.

As long as we use a {class}`DirectoryNode` with the same `root_dir` and `pattern` in
both tasks, pytask will automatically recognize that the second task depends on the
first. If that is not true, you might need to make this dependency more explicit by
using {func}`@task(after=...) <pytask.task>`, which is explained {ref}`here <after>`.

## Task generators

Coming to the last use case, what if we wanted to process each of the downloaded files
separately instead of dealing with them in one task?

We have to write a task generator to define an unknown number of tasks for an unknown
number of downloaded files.

A task generator is a task function in which we define more tasks, just as if we were
writing functions in a normal task module.

As an example, each task takes one of the downloaded files and copies its content to a
`.txt` file.

```{literalinclude} ../../../docs_src/how_to_guides/delayed_tasks_task_generator.py
```
