from pathlib import Path

import pytask
from pytask import Product
from typing_extensions import Annotated


for seed in range(10):

    @pytask.mark.task
    def task_create_random_data(
        path: Annotated[Path, Product] = Path(f"data_{seed}.pkl"), seed: int = seed
    ) -> None:
        ...
