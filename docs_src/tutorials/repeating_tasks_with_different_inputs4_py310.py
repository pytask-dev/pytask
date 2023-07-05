from pathlib import Path
from typing import Annotated

import pytask
from pytask import Product


for seed, id_ in ((0, "first"), (1, "second")):

    @pytask.mark.task(id=id_)
    def task_create_random_data(
        seed: int = seed,
        path_to_data: Annotated[Path, Product] = Path(f"data_{seed}.txt"),
    ) -> None:
        ...
