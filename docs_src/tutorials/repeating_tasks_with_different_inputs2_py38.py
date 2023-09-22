from pathlib import Path

from my_project.config import SRC
from pytask import Product
from pytask import task
from typing_extensions import Annotated


for seed in range(10):

    @task
    def task_create_random_data(
        path_to_parameters: Path = SRC / "parameters.yml",
        path_to_data: Annotated[Path, Product] = Path(f"data_{seed}.pkl"),
        seed: int = seed,
    ) -> None:
        ...
