from pathlib import Path
from typing import Annotated

from pytask import Product
from pytask import task

for seed in range(10):

    @task
    def task_create_random_data(
        path: Annotated[Path, Product] = Path(f"data_{seed}.pkl"), seed: int = seed
    ) -> None: ...
