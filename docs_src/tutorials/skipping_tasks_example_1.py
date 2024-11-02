from pathlib import Path
from typing import Annotated

import pytask
from pytask import Product


@pytask.mark.skip()
def task_long_running(
    path: Annotated[Path, Product] = Path("time_intensive_product.pkl"),
) -> None: ...
