# Migrate from scripts to pytask

Many people like you use executable scripts to manage tasks in their research workflows.
Although it bears a certain simplicity, there are many reasons why you should switch to
pytask.

- **Lazy builds**. Only execute the scripts that need to be re-run because something has
  changed.
- **Parallelization**. With
- [pytask-parallel](https://github.com/pytask-dev/pytask-parallel) you, can parallelize
- the execution of your scripts, giving you an extra speedup.
- pytask has many other features like [debugging](../tutorials/debugging.md) or
  [task selection](../tutorials/selecting_tasks.md).

Even if you do not use pytask's other features initially, the speedup will help you
develop quicker and reduce the time spent on optimizing your code.

## Installation

First, let us install pytask and pytask-parallel either with pip or conda.

```console
$ pip install pytask pytask-parallel

$ conda -c conda-forge pytask pytask-parallel
```

## Conversion to tasks

Next, we need to rewrite your scripts and move the executable part to a task function.
You might contain the code in the main namespace of your script like

```python
# Content of task_data_management.py
import pandas as pd


df = pd.read_csv("data.csv")

# Many operations.

df.to_pickle("data.pkl")
```

or you might use an `if __name__ == "__main__"` block like

```python
# Content of task_data_management.py
import pandas as pd


def main():
    df = pd.read_csv("data.csv")

    # Many operations.

    df.to_pickle("data.pkl")


if __name__ == "__main__":
    main()
```

Regardless of your choice, convert your scripts to this structure.

```python
# Content of task_data_management.py
import pandas as pd


def task_prepare_data():
    df = pd.read_csv("data.csv")

    # Many operations.

    df.to_pickle("data.pkl")
```

## Extracting dependencies and products

pytask needs to know in which order it has to execute the tasks and when to re-run them.
It infers this information automatically if you assign dependencies and products to a
task. Use `@pytask.mark.depends_on` for dependencies and `@pytask.mark.produces` for
products.

Rewriting our example yields this.

```python
# Content of task_data_management.py
import pandas as pd
import pytask


@pytask.mark.depends_on("data.csv")
@pytask.mark.produces("data.pkl")
def task_prepare_data(depends_on, produces):
    df = pd.read_csv(depends_on)

    # Many operations.

    df.to_pickle(produces)
```

Using the decorators, you can use `depends_on` and `produces` as arguments to the
function and access the paths to the dependencies and products as {class}`pathlib.Path`.

Pass a dictionary to the decorators if you have multiple dependencies or products. The
dictionary's keys are the dependencies' names, and the values are the paths. Here is an
example for multiple dependencies, but it applies similarly to products.

```python
import pandas as pd
import pytask


@pytask.mark.depends_on({"data_1": "data_1.csv", "data_2": "data_2.csv"})
@pytask.mark.produces("data.pkl")
def task_merge_data(depends_on, produces):
    df1 = pd.read_csv(depends_on["data_1"])
    df2 = pd.read_csv(depends_on["data_2"])

    df = df1.merge(df2, on=...)

    df.to_pickle(produces)
```

:::{seealso}
If you want to learn more about dependencies and products, read the
[tutorial](../tutorials/defining_dependencies_products.md).
:::

## Execution

At last, execute your newly defined tasks with pytask. Assuming your scripts lie in the
current directory of your terminal or a subsequent directory, run the following.

```{include} ../_static/md/migrate-from-scripts-to-pytask.md
```

Otherwise, pass the paths explicitly to the pytask executable.

If you have rewritten multiple scripts that can be run in parallel, use the
`-n/--n-workers` option to define the number of parallel tasks. pytask-parallel will
then automatically spawn multiple processes to run tasks in parallel.

```console
$ pytask -n 4
```

:::{seealso}
You can find more information on pytask-parallel in the
[readme](https://github.com/pytask-dev/pytask-parallel) on Github.
:::
