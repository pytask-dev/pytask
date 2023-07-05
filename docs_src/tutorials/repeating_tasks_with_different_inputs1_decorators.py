from pathlib import Path

import pytask


for seed in range(10):

    @pytask.mark.task
    @pytask.mark.produces(Path(f"data_{seed}.pkl"))
    def task_create_random_data(produces: Path, seed: int = seed) -> None:
        ...
