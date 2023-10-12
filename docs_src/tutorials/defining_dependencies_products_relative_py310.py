from pathlib import Path
from typing import Annotated

from pytask import Product


def task_create_random_data(
    path_to_data: Annotated[Path, Product] = Path("../bld/data.pkl")
) -> None:
    ...
