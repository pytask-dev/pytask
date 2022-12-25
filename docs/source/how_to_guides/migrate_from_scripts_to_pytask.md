# Migrate from scripts to pytask

Welcome to pytask! Are you tired of managing tasks in your research workflows with
scripts that get harder to maintain over time? Then pytask is here to help!

With pytask, you can enjoy features like:

- **Lazy builds**. Only execute the scripts that need to be run or re-run because
  something has changed, saving you lots of time.
- **Parallelization**. Use
  [pytask-parallel](https://github.com/pytask-dev/pytask-parallel) to speed up your
  scripts by running them in parallel.
- **Other features**. [Debugging](../tutorials/debugging.md) or
  [task selection](../tutorials/selecting_tasks.md).

And even if you don't use pytask's other features initially, the speedup alone will help
you develop quicker and focus on other things.

## Installation

To get started with pytask, simply install it with pip or conda:

```console
$ pip install pytask pytask-parallel

$ conda -c conda-forge pytask pytask-parallel
```

## Conversion to tasks

Next, we need to rewrite your scripts and move the executable part to a task function.
You might contain the code in the main namespace of your script like in this example.

```python
# Content of task_data_management.py
import pandas as pd


df = pd.read_csv("data.csv")

# Many operations.

df.to_pickle("data.pkl")
```

Or, you might use an `if __name__ == "__main__"` block like this example.

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

In both instances, you need to move your code into a task function.

```python
# Content of task_data_management.py
import pandas as pd


def task_prepare_data():
    df = pd.read_csv("data.csv")

    # Many operations.

    df.to_pickle("data.pkl")
```

## Extracting dependencies and products

To let pytask know the order in which to execute tasks and when to re-run them, you'll
need to specify task dependencies and products using `@pytask.mark.depends_on` and
`@pytask.mark.produces`. For that, extract the paths to the inputs and outputs of your
script and pass them to the decorator. For example:

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

The decorators allow you to use `depends_on` and `produces` as arguments to the
function and access the paths to the dependencies and products as {class}`pathlib.Path`.

You can pass a dictionary to these decorators if you have multiple dependencies or
products. The dictionary's keys are the dependencies'/product's names, and the values
are the paths. Here is an example:

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

Finally, execute your newly defined tasks with pytask. Assuming your scripts lie in the
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
