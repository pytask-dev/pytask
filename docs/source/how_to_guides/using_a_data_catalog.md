# Using a data catalog

A data catalog is an inventory for your project's data. You can add your data to the
catalog and then easily add them to your task functions.

The catalog can also handle data produced by your tasks automatically so that you do not
have to define any paths.

Lastly, after data has been added to catalog, you can import the catalog in a script or
Jupyter notebook and load the data for exploration.

## The `DataCatalog`

As an example, we build a workflow comprising of two tasks that do the following
actions.

1. Read in data from a text file, `input.txt` and storing the text as a pickle file.
1. Read the data from pickle, adding additional text and storing it as a text file under
   `output.txt`.

At first, we create the file `input.txt` and add some content.

```pycon
>>> from pathlib import Path
>>> Path("input.txt").write_text("Hello, ")
```

Secondly, we build the data catalog in a file separate from our task modules like
`config.py`, so we can import the data catalog everywhere. Register your data here. You
can add nodes, objects that are converted to nodes like `~pathlib.Path` or any other
object.

```python
# Content of config.py.
from pathlib import Path

from pytask import DataCatalog


# Create the data catalog.
data_catalog = DataCatalog()

# Register the input and the output data. Paths are assumed to be
# relative to the module where the data catalog is instantiated.
data_catalog.add("input", Path("input.txt"))
data_catalog.add("output", Path("output.txt"))
```

Next, let us define the two tasks. We are using return annotations for the second task
that are explained in this [guide](using_task_returns.md), but you can use any approach
from [../tutorials/defining_dependencies_products.md].

```python
def task_save_text_with_pickle(
    path: Annotated[Path, data_catalog["input"]]
) -> Annotated[str, data_catalog["intermediate"]]:
    text = path.read_text()
    return text


def task_add_content_and_save_text(
    text: Annotated[str, data_catalog["intermediate"]]
) -> Annotated[str, data_catalog["output"]]:
    text += "World!"
    return text
```

The important bit here is that we reference the intermediate pickle file in the
annotation `Annotated[str, data_catalog["intermediate"]]`. Since the entry
`"intermediate"` does not exist, the catalog creates a {class}`~pytask.PickleNode` for
this entry and saves the pickle file in a `.pytask` directory. The annotated type of the
variable is {obj}`str`, since we store and load a string from the pickle file.

Now, we can execute the tasks.

```{include} ../_static/md/using-a-data-catalog.md
```

## Developing with the `DataCatalog`

After you executed the workflow, you can import the data catalog in a Jupyter notebook
or in the terminal in the Python interpreter. Call the {meth}`~pytask.PNode.load` method
of a node to access its value.

```pycon
>>> from task_create_text import data_catalog
>>> data_catalog.entries
['pickle_file', 'input', 'output']
>>> data_catalog["intermediate"].load()
'Hello, World!'
>>> data_catalog["output"].load()
WindowsPath('C:\Users\pytask-dev\git\my_project\output.txt')
```

`data_catalog["intermediate"]` was stored with a {class}`~pytask.PickleNode` and returns
text whereas {class}`pathlib.Path`s become {class}`~pytask.PathNode`s and return their
path.

:::{note}
Whether the module `task_create_text.py` is importable depends on whether it is on your
`PYTHONPATH`, a variable that defines where modules can be found. If you develop your
workflow as a Python package as explained in the tutorials, then, you can import the
data catalog with `from myproject.config import data_catalog`.
:::

## Changing the default node

The data catalog uses the {class}`~pytask.PickleNode` by default to serialize any kind
of Python object. You can use any other node that follows the {protocol}`~pytask.PNode`
protocol and register it when creating the data catalog.

For example, use the {class}`~pytask.PythonNode` as the default.

```python
from pytask import PythonNode


data_catalog = DataCatalog(default_node=PythonNode)
```

Or, learn to write your own node by reading {doc}`writing_custom_nodes`.

## Changing the name and the default path

By default, the data catalogs store their data in a directory `.pytask/data_catalogs`.
If you use a `pyproject.toml` with a `[tool.pytask.ini_options]` section, then the
`.pytask` folder is in the same folder as the configuration file.

The default name for a catalog is `"default"` and so you will find its data in
`.pytask/data_catalogs/default`. If you assign a different name like
`"data_management"`, you will find the data in `.pytask/data_catalogs/data_management`.

```python
data_catalog = DataCatalog(name="data_management")
```

You can also change the path where the data catalogs will be stored by changing the
`path` attribute. Here, we store the data catalog's data next to the module where the
data catalog is defined in `.data`.

```python
from pathlib import Path


data_catalog = DataCatalog(path=Path(__file__).parent / ".data")
```

## Multiple data catalogs

You can use multiple data catalogs when you want to separate your datasets across
multiple catalogs or when you want to use the same names multiple times (although it is
not recommended!).

Make sure you assign different names to the data catalogs so that their data is stored
in different directories.

```python
# Stored in .pytask/data_catalog/a
data_catalog = DataCatalog(name="a")

# Stored in .pytask/data_catalog/b
data_catalog = DataCatalog(name="b")
```

Or, use different paths as explained above.
