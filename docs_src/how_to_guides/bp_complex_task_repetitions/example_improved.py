from pathlib import Path
from typing import Annotated

from myproject.config import EXPERIMENTS
from pytask import Product
from pytask import task

for experiment in EXPERIMENTS:

    @task(id=experiment.name)
    def task_fit_model(
        path_to_data: experiment.dataset.path,
        path_to_model: Annotated[Path, Product] = experiment.path,
    ) -> None: ...
