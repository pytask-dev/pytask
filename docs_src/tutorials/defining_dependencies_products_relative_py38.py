from pathlib import Path

from pytask import Product
from typing_extensions import Annotated


def task_create_random_data(
    path_to_data: Annotated[Path, Product] = Path("../bld/data.pkl")
) -> None:
    ...
