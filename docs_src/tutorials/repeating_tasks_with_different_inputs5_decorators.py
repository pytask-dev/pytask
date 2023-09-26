from pathlib import Path
from typing import NamedTuple

from pytask import task


class _Arguments(NamedTuple):
    seed: int
    path_to_data: Path


ID_TO_KWARGS = {
    "first": _Arguments(seed=0, path_to_data=Path("data_0.pkl")),
    "second": _Arguments(seed=1, path_to_data=Path("data_1.pkl")),
}


for id_, kwargs in ID_TO_KWARGS.items():

    @task(id=id_)
    def task_create_random_data(
        seed: int = kwargs["seed"], produces: Path = kwargs["produces"]
    ) -> None:
        ...