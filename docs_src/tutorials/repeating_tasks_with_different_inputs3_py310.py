from pathlib import Path
from typing import Annotated

import pytask
from pytask import Product


for seed in ((0,), (1,)):

    @pytask.mark.task
    def task_create_random_data(
        seed: tuple[int] = seed,
        path_to_data: Annotated[Path, Product] = Path(f"data_{seed[0]}.pkl"),
    ) -> None:
        ...
