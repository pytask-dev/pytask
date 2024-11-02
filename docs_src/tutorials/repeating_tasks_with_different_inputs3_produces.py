from pathlib import Path

from pytask import task

for seed in ((0,), (1,)):

    @task
    def task_create_random_data(
        produces: Path = Path(f"data_{seed[0]}.pkl"), seed: tuple[int] = seed
    ) -> None: ...
