# Using a data catalog

The [previous tutorial](defining_dependencies_products.md) explained how to use paths to
define dependencies and products.

Two things will quickly become a nuisance in bigger projects.

1. We have to define the same paths again and again.
1. We have to define paths to files that we are not particularly interested in since
   they are just intermediate representations.

As a solution, pytask offers a {class}`~pytask.DataCatalog` which is a purely optional
feature. The tutorial focuses on the main features. To learn about all the features,
read the [how-to guide](../how_to_guides/the_data_catalog.md).

Let us focus on the previous example and see how the {class}`~pytask.DataCatalog` helps
us.

The project structure is the same as in the previous example except the `.pytask` folder
and the missing `data.pkl` in `bld`.

```text
my_project
│
├───.pytask
│
├───bld
│   └────plot.png
│
├───src
│   └───my_project
│       ├────__init__.py
│       ├────config.py
│       ├────task_data_preparation.py
│       └────task_plot_data.py
│
└───pyproject.toml
```

## The `DataCatalog`

At first, we define the data catalog in `config.py`.

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_1.py
```

## `task_create_random_data`

Next, we look at the module `task_data_preparation.py` and its task
`task_create_random_data`. The task creates a dataframe with simulated data that should
be stored on the disk.

In the previous tutorial, we learned to use {class}`~pathlib.Path`s to define products
of our tasks. Here we see again the signature of the task function.

`````{tab-set}

````{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_py310.py
:lines: 10-12
```
````

````{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_py38.py
:lines: 10-12
```
````

````{tab-item} produces
:sync: produces

```{literalinclude} ../../../docs_src/tutorials/defining_dependencies_products_products_produces.py
:lines: 8
```
````
`````

When we want to use the data catalog, we replace `BLD / "data.pkl"` with an entry of the
data catalog like `data_catalog["data"]`. If there is yet no entry with the name
`"data"`, the data catalog will automatically create a {class}`~pytask.PickleNode`. The
node allows you to save any Python object to a `pickle` file.

You probably noticed that we did not need to define a path. That is because the data
catalog takes care of that and stores the `pickle` file in the `.pytask` folder.

Using `data_catalog["data"]` is thus equivalent to using `PickleNode(path=Path(...))`.

The following tabs show you how to use the data catalog given the interface you prefer.

`````{tab-set}

````{tab-item} Python 3.10+
:sync: python310plus

Use `data_catalog["data"]` as an default argument to access the
{class}`~pytask.PickleNode` within the task. When you are done transforming your
{class}`~pandas.DataFrame`, save it with {meth}`~pytask.PickleNode.save`.

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_2_py310.py
:emphasize-lines: 11, 22
```

````

````{tab-item} Python 3.8+
:sync: python38plus

Use `data_catalog["data"]` as an default argument to access the
{class}`~pytask.PickleNode` within the task. When you are done transforming your
{class}`~pandas.DataFrame`, save it with {meth}`~pytask.PickleNode.save`.

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_2_py38.py
:emphasize-lines: 10, 21
```

````

````{tab-item} ​produces
:sync: produces

Use `data_catalog["data"]` as an default argument to access the
{class}`~pytask.PickleNode` within the task. When you are done transforming your
{class}`~pandas.DataFrame`, save it with {meth}`~pytask.PickleNode.save`.

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_2_produces.py
:emphasize-lines: 7, 17
```

````

````{tab-item} ​Python 3.10+ & Return
:sync: return

An elegant way to use the data catalog is via return type annotations. Add
`data_catalog["data"]` to the annotated return and simply return the
{class}`~pandas.DataFrame` to store it.

You can read more about return type annotations in
[Using task returns](../how_to_guides/using_task_returns.md).

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_2_py310_return.py
:emphasize-lines: 8, 17
```

````
`````

## `task_plot_data`

Next, we will define the second task that consumes the data set from the previous task.
Following one of the interfaces gives you immediate access to the
{class}`~pandas.DataFrame` in the task without any additional line to load it.

`````{tab-set}

````{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_3_py310.py
:emphasize-lines: 12
```

````

````{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_3_py38.py
:emphasize-lines: 12
```

````
`````

Finally, let's execute the two tasks.

```{include} ../_static/md/defining-dependencies-products.md
```

## Adding data to the catalog

In most projects, you have other data sets that you would like to access via the data
catalog. To add them, call the {meth}`~pytask.DataCatalog.add` method and supply a name
and a path.

Let's add `file.csv` with the name `"csv"` to the data catalog and use it to create
`data["transformed_csv"]`.

```text
my_project
│
├───pyproject.toml
│
├───src
│   └───my_project
│       ├────config.py
│       ├────file.csv
│       ├────task_data_preparation.py
│       └────task_plot_data.py
│
├───.pytask
│   └────...
│
└───bld
    ├────file.pkl
    └────plot.png
```

We can use a relative or an absolute path to define the location of the file. A relative
path means the location is relative to the module of the data catalog.

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_4.py
```

You can now use the data catalog as in the previous example and use the
{class}`~pathlib.Path` in the task.

```{note}
Note that the value of `data_catalog["csv"]` inside the task becomes a
{class}`~pathlib.Path`. It is because a {class}`~pathlib.Path` in
{meth}`~pytask.DataCatalog.add` is not parsed to a {class}`~pytask.PickleNode` but a
{class}`~pytask.PathNode`.

Read {doc}`../how_to_guides/writing_custom_nodes` for more information about
different node types which is not relevant now.
```

`````{tab-set}

````{tab-item} Python 3.10+
:sync: python310plus

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_5_py310.py
:emphasize-lines: 11, 12
```

````

````{tab-item} Python 3.8+
:sync: python38plus

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_5_py38.py
:emphasize-lines: 11, 12
```

````

````{tab-item} ​Python 3.10+ & Return
:sync: return

```{literalinclude} ../../../docs_src/tutorials/using_a_data_catalog_5_py310_return.py
:emphasize-lines: 9, 10
```

````
`````

## Developing with the `DataCatalog`

You can also use the data catalog in a Jupyter Notebook or the terminal in the Python
interpreter. This can be super helpful when you develop tasks interactively in a Jupyter
Notebook.

Simply import the data catalog, select a node and call the {meth}`~pytask.PNode.load`
method of a node to access its value.

Here is an example with a terminal.

```pycon
>>> from myproject.config import data_catalog
>>> data_catalog.entries
['csv', 'data', 'transformed_csv']
>>> data_catalog["data"].load()
DataFrame(...)
>>> data_catalog["csv"].load()
WindowsPath('C:\Users\pytask-dev\git\my_project\file.csv')
```

`data_catalog["data"]` was stored with a {class}`~pytask.PickleNode` and returns the
{class}`~pandas.DataFrame` whereas `data_catalog["csv"]` becomes a
{class}`~pytask.PathNode` and {meth}`~pytask.PNode.load` returns the path.
