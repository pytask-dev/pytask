from pathlib import Path
from typing import Tuple

from pytask import task

for seed in ((0,), (1,)):

    @task
    def task_create_random_data(
        produces: Path = Path(f"data_{seed[0]}.pkl"), seed: Tuple[int] = seed
    ) -> None: ...
