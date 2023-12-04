from pathlib import Path
from typing import Annotated

from pytask import Product


def task_write_file(path: Annotated[Path, Product] = Path("file.txt")) -> None:
    path.touch()
