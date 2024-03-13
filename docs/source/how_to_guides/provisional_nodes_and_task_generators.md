# Provisional nodes and task generators

pytask's execution model can usually be separated into three phases.

1. Collection of tasks, dependencies, and products.
1. Building the DAG.
1. Executing the tasks.

But, in some situations, pytask needs to be more flexible.

Imagine you want to download a folder with files from an online storage. Before the task
is completed you do not know the total number of files or their filenames. How can you
still describe the files as products of the task?

And how would you define another task that depends on these files?

The following sections will explain how you use pytask in these situations.

## Producing provisional nodes

As an example for the aforementioned scenario, let us write a task that downloads all
files without a file extension from the root folder of the pytask GitHub repository. The
files are downloaded to a folder called `downloads`. `downloads` is in the same folder
as the task module because it is a relative path.

```{literalinclude} ../../../docs_src/how_to_guides/provisional_products.py
---
emphasize-lines: 4, 22
---
```

Since the names of the files are not known when pytask is started, we need to use a
{class}`~pytask.DirectoryNode` to define the task's product. With a
{class}`~pytask.DirectoryNode` we can specify where pytask can find the files. The files
are described with a root path (default is the directory of the task module) and a glob
pattern (default is `*`).

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

The difficulty here is how can we reference the downloaded files before they have been
downloaded.

```{literalinclude} ../../../docs_src/how_to_guides/provisional_task.py
---
emphasize-lines: 9
---
```

To reference the files that will be downloaded, we use the
{class}`~pytask.DirectoryNode` is a dependency. Before the task is executed, the list of
files in the folder defined by the root path and the pattern are automatically collected
and passed to the task.

If we use a {class}`~pytask.DirectoryNode` with the same `root_dir` and `pattern` in
both tasks, pytask will automatically recognize that the second task depends on the
first. If that is not true, you might need to make this dependency more explicit by
using {func}`@task(after=...) <pytask.task>`, which is explained {ref}`here <after>`.

## Task generators

What if we wanted to process each downloaded file separately instead of dealing with
them in one task?

For that, we have to write a task generator to define an unknown number of tasks for an
unknown number of downloaded files.

A task generator is a task function in which we define more tasks, just as if we were
writing functions in a task module.

The code snippet shows each task takes one of the downloaded files and copies its
content to a `.txt` file.

```{literalinclude} ../../../docs_src/how_to_guides/provisional_task_generator.py
```

```{important}
The generated tasks need to be decoratored with {func}`@task <pytask.task>` to be
collected.
```
