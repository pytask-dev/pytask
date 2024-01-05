from pathlib import Path
from typing import Annotated

from pytask import Product


def task_write_file(
    input_path: Path = Path("in.txt"),
    output_path: Annotated[Path, Product] = Path("out.txt"),
) -> None:
    output_path.write_text(input_path.read_text())
