from pathlib import Path

import pytask
from pytask import Product
from typing_extensions import Annotated


@pytask.mark.skip()
def task_long_running(
    path: Annotated[Path, Product] = Path("time_intensive_product.pkl")
) -> None:
    ...
