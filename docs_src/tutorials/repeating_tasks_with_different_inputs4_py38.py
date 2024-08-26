from pathlib import Path

from typing_extensions import Annotated

from pytask import Product
from pytask import task

for seed, id_ in ((0, "first"), (1, "second")):

    @task(id=id_)
    def task_create_random_data(
        seed: int = seed,
        path_to_data: Annotated[Path, Product] = Path(f"data_{seed}.txt"),
    ) -> None: ...
