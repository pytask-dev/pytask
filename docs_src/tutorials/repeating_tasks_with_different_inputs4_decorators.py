from pathlib import Path

import pytask
from pytask import task


for seed, id_ in ((0, "first"), (1, "second")):

    @task(id=id_)
    @pytask.mark.produces(Path(f"out_{seed}.txt"))
    def task_create_random_data(produces: Path, seed: int = seed) -> None:
        ...
