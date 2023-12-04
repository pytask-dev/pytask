from pathlib import Path
from typing import Annotated

from pytask import PathNode


def task_example(path: Annotated[Path, PathNode(path=Path("input.txt"))]) -> None:
    ...
