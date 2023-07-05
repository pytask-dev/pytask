from pathlib import Path

import pytask
from my_project.config import SRC


for seed in range(10):

    @pytask.mark.task
    @pytask.mark.depends_on(SRC / "parameters.yml")
    @pytask.mark.produces(f"data_{seed}.pkl")
    def task_create_random_data(
        depends_on: Path, produces: Path, seed: int = seed
    ) -> None:
        ...
