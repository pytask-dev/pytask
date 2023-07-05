from pathlib import Path
from typing import Tuple

import pytask


for seed in ((0,), (1,)):

    @pytask.mark.task
    @pytask.mark.produces(Path(f"data_{seed[0]}.pkl"))
    def task_create_random_data(produces: Path, seed: Tuple[int] = seed) -> None:
        ...
