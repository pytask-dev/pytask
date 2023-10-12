from pathlib import Path
from typing import Annotated

from pytask import Product


def task_example(
    text: str = "Hello, World", path: Annotated[Path, Product] = Path("file.txt")
) -> None:
    path.write_text(text)
