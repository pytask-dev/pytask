from pathlib import Path
from typing import Annotated

from pytask import Product
from pytask import task

for seed in ((0,), (1,)):

    @task
    def task_create_random_data(
        seed: tuple[int] = seed,
        path_to_data: Annotated[Path, Product] = Path(f"data_{seed[0]}.pkl"),
    ) -> None: ...
