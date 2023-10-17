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

1. Read in data from a text file, `input.txt` and storing it as a pickle file.
1. Read the data from pickle, adding additional text and storing it as a text file under
   `output.txt`.

At first, we build the data catalog by registering the data that we provide or that we
later want to access.

```python
from pathlib import Path

from pytask import DataCatalog
from pytask import PathNode


# Create the data catalog.
data_catalog = DataCatalog()

# Register the input and the output data. Paths are assumed to be
# relative to the module where the data catalog is instantiated.
data_catalog.add("input", Path("input.txt"))
data_catalog.add("output", Path("output.txt"))
```

We also have to create `input.txt` and add some content like `Hello, `.

We do not register the intermediate pickle file, yet.

Next, let us define the two tasks.

```python
def task_save_text_with_pickle(
    path: Annotated[Path, data_catalog["input"]]
) -> Annotated[str, data_catalog["pickle_file"]]:
    text = path.read_text()
    return text


def task_add_content_and_save_text(
    text: Annotated[str, data_catalog["pickle_file"]]
) -> Annotated[str, data_catalog["output"]]:
    text += "World!"
    return text
```

The important bit here is that we reference the intermediate pickle file with
`data_catalog["pickle_file"]`. Since the entry does not exist, the catalog creates a
{class}`~pytask.PickleNode` for this entry and saves the pickle file in the directory
given to the {class}`~pytask.DataCatalog`.

Now, we can execute the tasks.

```{include} ../_static/md/using-a-data-catalog.md
```

## Developing with the `DataCatalog`

After you executed the workflow, you can import the data catalog in a Jupyter notebook
or in the terminal in the Python interpreter. Call the {meth}`~pytask.PNode.load` method
of a node to access its value.

```pycon
>>> from task_data_catalog import data_catalog
>>> data_catalog.entries
['new_content', 'file', 'output']
>>> data_catalog["new_content"].load()
'This is the text.World!'
>>> data_catalog["output"].load()
WindowsPath('C:\Users\pytask-dev\git\my_project\output.txt')
```

`data_catalog["new_content"]` was stored with a {class}`~pytask.PickleNode` and returns
text whereas {class}`pathlib.Path`s become {class}`~pytask.PathNode`s and return their
path.

## Changing the default node

The data catalog uses the {class}`~pytask.PickleNode` by default to serialize any kind
of Python object. You can use any other node that follows the {protocol}`~pytask.PNode`
protocol and register it when creating the data catalog.

For example, use the {class}`~pytask.PythonNode` as the default.

```python
from pytask import PythonNode


data_catalog = DataCatalog(default_node=PythonNode)
```

```{seealso}
If you want to learn more about custom nodes, read {doc}`writing_custom_nodes`.
```
