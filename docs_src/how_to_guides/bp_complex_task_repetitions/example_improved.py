from typing import Annotated
from typing import Any

from myproject.config import EXPERIMENTS
from myproject.config import data_catalog
from pytask import task

for experiment in EXPERIMENTS:

    @task(id=experiment.name)
    def task_fit_model(
        path_to_data: experiment.dataset.path,
    ) -> Annotated[Any, data_catalog[experiment.fitted_model_name]]: ...
