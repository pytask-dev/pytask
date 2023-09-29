from pathlib import Path

from pytask import task


for seed, id_ in ((0, "first"), (1, "second")):

    @task(id=id_)
    def task_create_random_data(
        produces: Path = Path(f"out_{seed}.txt"), seed: int = seed
    ) -> None:
        ...
