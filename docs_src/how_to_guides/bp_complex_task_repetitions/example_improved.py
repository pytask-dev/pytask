from pathlib import Path
from typing import Annotated
from typing import Any

from myproject.config import EXPERIMENTS
from myproject.config import Model
from myproject.config import data_catalog

from _pytask.nodes import PythonNode
from pytask import task

for experiment in EXPERIMENTS:

    @task(id=experiment.name)
    def task_fit_model(
        model: Annotated[Model, PythonNode(hash=True)] = experiment.model,
        path_to_data: Path = experiment.dataset.path,
    ) -> Annotated[Any, data_catalog[experiment.fitted_model_name]]: ...
