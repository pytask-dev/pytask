"""Contains an example of how to use the data catalog."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pytask import DataCatalog


_SRC = Path(__file__).parent.resolve()

# Generate input data


_DataCatalog = DataCatalog()
_DataCatalog.add("file", _SRC / "file.txt")
_DataCatalog.add("output", _SRC / "output.txt")


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
