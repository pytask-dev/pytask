from pathlib import Path

from pytask import task


for seed in range(10):

    @task
    def task_create_random_data(
        produces: Path = Path(f"data_{seed}.pkl"), seed: int = seed
    ) -> None:
        ...
