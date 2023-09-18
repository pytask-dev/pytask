# Using a data catalog

A data catalog is an abstraction layer to ease the data access for the user.

The following example shows:

- How data access is facilitated by a flat namespace in the data catalog.
- How some files like `_DataCatalog["new_content"]` are automatically saved whenever the
  user does not really care about where they are stored.

```python
"""Contains an example of how to use the data catalog."""
from pathlib import Path
from typing import Annotated
from _pytask.nodes import PathNode
from pytask import DataCatalog


_SRC = Path(__file__).parent.resolve()

# Generate input data
# _SRC.joinpath("file.txt").write_text("Hello, ")


_DataCatalog = DataCatalog()
_DataCatalog.add("file", PathNode.from_path(_SRC / "file.txt"))
_DataCatalog.add("output", PathNode.from_path(_SRC / "output.txt"))


def task_add_content(
    path: Annotated[Path, _DataCatalog["file"]]
) -> Annotated[str, _DataCatalog["new_content"]]:
    text = path.read_text()
    text += "World!"
    return text


def task_save_text(
    text: Annotated[str, _DataCatalog["new_content"]]
) -> Annotated[str, _DataCatalog["output"]]:
    return text
```
