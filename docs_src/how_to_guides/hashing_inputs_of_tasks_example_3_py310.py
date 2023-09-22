import json
from pathlib import Path
from typing import Annotated
from typing import Any

from deepdiff import DeepHash
from pytask import Product
from pytask import PythonNode


def calculate_hash(x: Any) -> str:
    return DeepHash(x)[x]


node = PythonNode({"a": 1, "b": 2}, hash=calculate_hash)


def task_example(
    data: Annotated[dict[str, int], node],
    path: Annotated[Path, Product] = Path("file.txt"),
) -> None:
    path.write_text(json.dumps(data))
