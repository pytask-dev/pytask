from pathlib import Path
from typing import Annotated

from pytask import PathNode
from pytask import Product


def task_write_file(
    path: Annotated[Path, PathNode(path=Path("file.txt")), Product],
) -> None:
    path.touch()
