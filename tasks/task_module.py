from pathlib import Path
from typing import Annotated
from pytask import Product


def task_example(path: Annotated[Path, Product] = Path("out.txt")) -> None:
    path.write_text("Hello World!")
