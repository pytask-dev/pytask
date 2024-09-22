from pathlib import Path

from my_project.config import SRC

from pytask import task

for seed in range(10):

    @task
    def task_create_random_data(
        path_to_parameters: Path = SRC / "parameters.yml",
        produces: Path = Path(f"data_{seed}.pkl"),
        seed: int = seed,
    ) -> None: ...
