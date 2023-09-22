from pathlib import Path
from typing import Annotated

from pytask import Product
from pytask import PythonNode


def task_example(
    text: Annotated[str, PythonNode("Hello, World", hash=True)],
    path: Annotated[Path, Product] = Path("file.txt"),
) -> None:
    path.write_text(text)
