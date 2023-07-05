from pathlib import Path
from typing import Annotated
from typing import NamedTuple

import pytask
from pytask import Product


class _Arguments(NamedTuple):
    seed: int
    path_to_data: Path


ID_TO_KWARGS = {
    "first": _Arguments(seed=0, path_to_data=Path("data_0.pkl")),
    "second": _Arguments(seed=1, path_to_data=Path("data_1.pkl")),
}


for id_, arguments in ID_TO_KWARGS.items():

    @pytask.mark.task(id=id_)
    def task_create_random_data(
        seed: int = arguments.seed,
        path_to_data: Annotated[Path, Product] = arguments.path_to_data,
    ) -> None:
        ...
