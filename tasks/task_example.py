from pathlib import Path
from typing import Annotated
from pytask import Product



def task_example(path: Path = Path("out.txt")) -> Annotated[Path, Path("out_2.txt")]:
    """Compute the square of 2.

    Example
    -------
    >>> task_example(2)
    4

    """
    return path.read_text()
