from pathlib import Path
from typing import Annotated

from pytask import Product


def task_create_output(
    path_in: Path = Path("input.txt"),
    path_out: Annotated[Path, Product] = Path("output.txt"),
) -> None:
    path_out.write_text(path_in.read_text().upper())
