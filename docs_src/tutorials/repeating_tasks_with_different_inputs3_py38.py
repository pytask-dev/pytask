from pathlib import Path
from typing import Tuple

import pytask
from pytask import Product
from typing_extensions import Annotated


for seed in ((0,), (1,)):

    @pytask.mark.task
    def task_create_random_data(
        seed: Tuple[int] = seed,
        path_to_data: Annotated[Path, Product] = Path(f"data_{seed[0]}.pkl"),
    ) -> None:
        ...
