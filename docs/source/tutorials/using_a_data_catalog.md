# Using a data catalog

The [previous tutorial](defining_dependencies_products.md) explained how to use paths to
define dependencies and products.

Two things will quickly become a nuisance in bigger projects.

1. We have to define the same paths again and again.
1. We have to define paths to files that we are not particularly interested in since
   they are just intermediate representations.

As a solution, pytask offers a `pytask.DataCatalog` which is a purely optional feature.
The tutorial focuses on the main features. To learn about all the features, read the
[how-to guide](../how_to_guides/the_data_catalog.md).

Let us focus on the previous example and see how the `pytask.DataCatalog` helps us.

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

```python
--8 < --"docs_src/tutorials/using_a_data_catalog_1.py"
```

## `task_create_random_data`

Next, we look at the module `task_data_preparation.py` and its task
`task_create_random_data`. The task creates a dataframe with simulated data that should
be stored on the disk.

In the previous tutorial, we learned to use `pathlib.Path`s to define products of our
tasks. Here we see again the signature of the task function.

=== "Annotated"

````
```python hl_lines="12"
--8<-- "docs_src/tutorials/defining_dependencies_products_products_py310.py"
```
````

=== "produces"

````
```python hl_lines="8"
--8<-- "docs_src/tutorials/defining_dependencies_products_products_produces.py"
```
````

When we want to use the data catalog, we replace `BLD / "data.pkl"` with an entry of the
data catalog like `data_catalog["data"]`. If there is yet no entry with the name
`"data"`, the data catalog will automatically create a `pytask.PickleNode`. The node
allows you to save any Python object to a `pickle` file.

You probably noticed that we did not need to define a path. That is because the data
catalog takes care of that and stores the `pickle` file in the `.pytask` folder.

Using `data_catalog["data"]` is thus equivalent to using `PickleNode(path=Path(...))`.

The following tabs show you how to use the data catalog given the interface you prefer.

=== "Annotated"

````
Use `data_catalog["data"]` as an default argument to access the
`pytask.PickleNode` within the task. When you are done transforming your
`pandas.DataFrame`, save it with `pytask.PickleNode.save`.

```python hl_lines="11 22"
--8<-- "docs_src/tutorials/using_a_data_catalog_2_py310.py"
```
````

=== "produces"

````
Use `data_catalog["data"]` as an default argument to access the
`pytask.PickleNode` within the task. When you are done transforming your
`pandas.DataFrame`, save it with `pytask.PickleNode.save`.

```python hl_lines="7 17"
--8<-- "docs_src/tutorials/using_a_data_catalog_2_produces.py"
```
````

=== "Annotated & Return"

````
An elegant way to use the data catalog is via return type annotations. Add
`data_catalog["data"]` to the annotated return and simply return the
`pandas.DataFrame` to store it.

You can read more about return type annotations in
[Using task returns](../how_to_guides/using_task_returns.md).

```python hl_lines="8 17"
--8<-- "docs_src/tutorials/using_a_data_catalog_2_py310_return.py"
```
````

## `task_plot_data`

Next, we will define the second task that consumes the data set from the previous task.
Following one of the interfaces gives you immediate access to the `pandas.DataFrame` in
the task without any additional line to load it.

```python hl_lines="13"
--8 < --"docs_src/tutorials/using_a_data_catalog_3_py310.py"
```

Finally, let's execute the two tasks.

--8\<-- "docs/source/\_static/md/defining-dependencies-products.md"

## Adding data to the catalog

In most projects, you have other data sets that you would like to access via the data
catalog. To add them, call the `pytask.DataCatalog.add` method and supply a name and a
path.

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

```python
--8 < --"docs_src/tutorials/using_a_data_catalog_4.py"
```

You can now use the data catalog as in the previous example and use the `pathlib.Path`
in the task.

!!! note

```
Note that the value of `data_catalog["csv"]` inside the task becomes a
`pathlib.Path`. It is because a `pathlib.Path` in
`pytask.DataCatalog.add` is not parsed to a `pytask.PickleNode` but a
`pytask.PathNode`.

Read [writing custom nodes](../how_to_guides/writing_custom_nodes.md) for more information about
different node types which is not relevant now.
```

=== "Annotated"

````
```python hl_lines="12 13"
--8<-- "docs_src/tutorials/using_a_data_catalog_5_py310.py"
```
````

=== "Annotated & Return"

````
```python hl_lines="9 10"
--8<-- "docs_src/tutorials/using_a_data_catalog_5_py310_return.py"
```
````

## Developing with the `DataCatalog`

You can also use the data catalog in a Jupyter Notebook or the terminal in the Python
interpreter. This can be super helpful when you develop tasks interactively in a Jupyter
Notebook.

Simply import the data catalog, select a node and call the `pytask.PNode.load` method of
a node to access its value.

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

`data_catalog["data"]` was stored with a `pytask.PickleNode` and returns the
`pandas.DataFrame` whereas `data_catalog["csv"]` becomes a `pytask.PathNode` and
`pytask.PNode.load` returns the path.
