from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pytask import Product
from pytask import task


@dataclass
class _Arguments:
    seed: int
    path_to_data: Path


ID_TO_KWARGS = {
    "first": _Arguments(seed=0, path_to_data=Path("data_0.pkl")),
    "second": _Arguments(seed=1, path_to_data=Path("data_1.pkl")),
}


for id_, kwargs in ID_TO_KWARGS.items():

    @task(id=id_, kwargs=kwargs)
    def task_create_random_data(
        seed: int, path_to_data: Annotated[Path, Product]
    ) -> None: ...
