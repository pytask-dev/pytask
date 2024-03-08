from pathlib import Path

from pytask import Product
from pytask import task
from typing_extensions import Annotated

for seed in range(10):

    @task
    def task_create_random_data(
        path: Annotated[Path, Product] = Path(f"data_{seed}.pkl"), seed: int = seed
    ) -> None: ...
