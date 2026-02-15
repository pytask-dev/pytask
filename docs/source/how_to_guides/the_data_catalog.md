# The `DataCatalog` - Revisited

This guide explains more details about the
[pytask.DataCatalog](../api/core_classes_and_exceptions.md#pytask.DataCatalog) that were
left out of the [tutorial](../tutorials/using_a_data_catalog.md). Please, read the
tutorial for a basic understanding.

## Changing the default node

The data catalog uses the
[pytask.PickleNode](../api/nodes_and_tasks.md#pytask.PickleNode) by default to serialize
any kind of Python object. You can use any other node that follows the
[pytask.PNode](../api/nodes_and_tasks.md#pytask.PNode) protocol and register it when
creating the data catalog.

For example, use the [pytask.PythonNode](../api/nodes_and_tasks.md#pytask.PythonNode) as
the default.

```python
from pytask import PythonNode
from pytask import DataCatalog


data_catalog = DataCatalog(default_node=PythonNode)
```

Or, learn to write your node by reading [writing custom nodes](writing_custom_nodes.md).

Here, is an example for a
[pytask.PickleNode](../api/nodes_and_tasks.md#pytask.PickleNode) that uses cloudpickle
instead of the normal `pickle` module.

```py
--8<-- "docs_src/how_to_guides/the_data_catalog.py"
```

## Changing the name and the default path

By default, data catalogs store their data in a directory `.pytask/data_catalogs`. If
you use a `pyproject.toml` with a `[tool.pytask.ini_options]` section, then the
`.pytask` folder is in the same folder as the configuration file.

The default name for a catalog is `"default"` and so you will find its data in
`.pytask/data_catalogs/default`. If you assign a different name like
`"data_management"`, you will find the data in `.pytask/data_catalogs/data_management`.

```python
from pytask import DataCatalog


data_catalog = DataCatalog(name="data_management")
```

!!! note

    The name of a data catalog is restricted to letters, numbers, hyphens and underscores.

You can also change the path where the data catalogs will be stored by changing the
`path` attribute. Here, we store the data catalog's data next to the module where the
data catalog is defined in `.data`.

```python
from pathlib import Path
from pytask import DataCatalog


data_catalog = DataCatalog(path=Path(__file__).parent / ".data")
```

## Multiple data catalogs

You can use multiple data catalogs when you want to separate your datasets or to avoid
name collisions of data catalog entries.

Make sure you assign different names to the data catalogs so that their data is stored
in different directories.

```python
from pytask import DataCatalog

# Stored in .pytask/data_catalog/a
data_catalog_a = DataCatalog(name="a")

# Stored in .pytask/data_catalog/b
data_catalog_b = DataCatalog(name="b")
```

Or, use different paths as explained above.

## Nested data catalogs

Name collisions can also occur when you are using multiple levels of repetitions, for
example, when you are fitting multiple models to multiple data sets.

You can structure your data catalogs like this.

```python
from pytask import DataCatalog


MODEL_NAMES = ("ols", "logistic_regression")
DATA_NAMES = ("data_1", "data_2")


nested_data_catalogs = {
    model_name: {
        data_name: DataCatalog(name=f"{model_name}-{data_name}")
        for data_name in DATA_NAMES
    }
    for model_name in MODEL_NAMES
}
```

The task could look like this.

```python
from pathlib import Path
from pytask import task
from typing import Annotated

from my_project.config import DATA_NAMES
from my_project.config import MODEL_NAMES
from my_project.config import nested_data_catalogs


for model_name in MODEL_NAMES:
    for data_name in DATA_NAMES:

        @task
        def fit_model(
            path: Path = Path("...", data_name),
        ) -> Annotated[
            Any, nested_data_catalogs[model_name][data_name]["fitted_model"]
        ]:
            data = ...
            fitted_model = ...
            return fitted_model
```
