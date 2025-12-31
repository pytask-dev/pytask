# Migrating from scripts to pytask

Are you tired of managing tasks in your research workflows with scripts that get harder
to maintain over time? Then pytask is here to help!

With pytask, you can enjoy features like:

- **Lazy builds**. Only execute the scripts that need to be run or re-run because
  something has changed, saving you lots of time.
- **Parallelization**. Use
  [pytask-parallel](https://github.com/pytask-dev/pytask-parallel) to speed up your
  scripts by running them in parallel.
- **Cross-language projects**. pytask has several plugins for running scripts written in
  other popular languages: [pytask-r](https://github.com/pytask-dev/pytask-r),
  [pytask-julia](https://github.com/pytask-dev/pytask-julia), and
  [pytask-stata](https://github.com/pytask-dev/pytask-stata).

The following guide will walk you through a series of steps to quickly migrate your
scripts to a workflow managed by pytask. The focus is first on Python scripts, but the
guide concludes with an additional example of an R script.

## Installation

To get started with pytask, install it with uv or pixi:

```console
$ uv add pytask pytask-parallel

$ pixi add pytask pytask-parallel
```

## From Python script to task

We must rewrite your scripts and move the executable part to a task function. You might
contain the code in the main namespace of your script, like in this example.

```{literalinclude} ../../../docs_src/how_to_guides/migrating_from_scripts_to_pytask_1.py
```

Or, you might use an `if __name__ == "__main__"` block like this example.

```{literalinclude} ../../../docs_src/how_to_guides/migrating_from_scripts_to_pytask_2.py
```

For pytask, you need to move the code into a task that is a function whose name starts
with `task_` in a module with the same prefix like `task_data_management.py`.

```{literalinclude} ../../../docs_src/how_to_guides/migrating_from_scripts_to_pytask_3.py
```

An `if __name__ == "__main__"` block must be deleted.

## Extracting dependencies and products

To let pytask know the order in which to execute tasks and when to re-run them, you'll
need to specify task dependencies and products. Add dependencies as arguments to the
function with default values. Do the same for products, but also add the special
{obj}`~pytask.Product` annotation with `Annotated[Path, Product]`. For example:

```{literalinclude} ../../../docs_src/how_to_guides/migrating_from_scripts_to_pytask_4.py
```

You can also use a dictionary to group multiple dependencies or products.

```{literalinclude} ../../../docs_src/how_to_guides/migrating_from_scripts_to_pytask_5.py
```

```{seealso}
If you want to learn more about dependencies and products, read the
[tutorial](../tutorials/defining_dependencies_products.md).
```

## Execution

Finally, execute your newly defined tasks with pytask. Assuming your scripts lie in the
current directory of your terminal or a subsequent directory, run the following.

```{include} ../_static/md/migrating-from-scripts-to-pytask.md
```

Otherwise, pass the paths explicitly to the pytask executable.

If you have rewritten multiple scripts that can be run in parallel, use the
`-n/--n-workers` option to define the number of parallel tasks. pytask-parallel will
then automatically spawn multiple processes to run the workflow in parallel.

```console
$ pytask -n 4
```

```{seealso}
You can find more information on pytask-parallel in the
[readme](https://github.com/pytask-dev/pytask-parallel) on Github.
```

## Bonus: From R script to task

pytask wants to help you get your job done, and sometimes a different programming
language can make your life easier. Thus, pytask has several plugins to integrate code
written in R, Julia, and Stata. Here, we explore how to incorporate an R script with
[pytask-r](https://github.com/pytask-dev/pytask-r). You can also find more information
about the plugin in the repo's readme.

First, we will install the package.

```console
$ uv add pytask-r

$ pixi add pytask-r
```

```{seealso}
Checkout [pytask-julia](https://github.com/pytask-dev/pytask-julia) and
[pytask-stata](https://github.com/pytask-dev/pytask-stata), too!
```

And here is the R script `prepare_data.r` that we want to integrate.

```r
# Content of prepare_data.r
df <- read.csv("data.csv")

# Many operations.

saveRDS(df, "data.rds")
```

Next, we create a task function to point pytask to the script and the dependencies and
products.

```{literalinclude} ../../../docs_src/how_to_guides/migrating_from_scripts_to_pytask_6.py
```

pytask automatically makes the paths to the dependencies and products available to the R
file via a JSON file. Let us amend the R script to load the information from the JSON
file.

```r
# Content of prepare_data.r
library(jsonlite)

# Read the JSON file whose path is passed to the script
args <- commandArgs(trailingOnly=TRUE)
path_to_json <- args[length(args)]
config <- read_json(path_to_json)

df <- read.csv(config$depends_on)

# Many operations.

saveRDS(df, config$produces)
```

## Conclusion

Congrats! You have just set up your first workflow with pytask!

If you enjoyed what you have seen, you should discover the other parts of the
documentation. The [tutorials](../tutorials/index.md) are a good entry point to start
with pytask and learn about many concepts step-by-step.
