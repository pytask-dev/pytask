# The `DataCatalog` - Revisited

An introduction to the data catalog can be found in the
[tutorial](../tutorials/using_a_data_catalog.md).

This guide explains some details that were left out of the tutorial.

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

Here, is an example for a `PickleNode` that uses cloudpickle instead of the normal
`pickle` module.

```{literalinclude} ../../../docs_src/how_to_guides/the_data_catalog.py
```

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
data_catalog_a = DataCatalog(name="a")

# Stored in .pytask/data_catalog/b
data_catalog_b = DataCatalog(name="b")
```

Or, use different paths as explained above.
