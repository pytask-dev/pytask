from pathlib import Path
from typing import Annotated

import pytask
from pytask import Product


for seed in range(10):

    @pytask.mark.task
    def task_create_random_data(
        path: Annotated[Path, Product] = Path(f"data_{seed}.pkl"), seed: int = seed
    ) -> None:
        ...
