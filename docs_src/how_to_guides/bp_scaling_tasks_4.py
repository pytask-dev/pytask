# Content of task_estimate_models.py
from pathlib import Path

from my_project.data_preparation.config import path_to_processed_data
from my_project.estimations.config import ESTIMATIONS
from my_project.estimations.config import path_to_estimation_result
from pytask import Product
from pytask import task
from typing_extensions import Annotated


def _create_parametrization(
    estimations: dict[str, dict[str, str]],
) -> dict[str, str | Path]:
    id_to_kwargs = {}
    for name, config in estimations.items():
        id_to_kwargs[name] = {
            "path_to_data": path_to_processed_data(config["data"]),
            "model": config["model"],
            "path_to_estimation": path_to_estimation_result(name),
        }

    return id_to_kwargs


_ID_TO_KWARGS = _create_parametrization(ESTIMATIONS)


for id_, kwargs in _ID_TO_KWARGS.items():

    @task(id=id_, kwargs=kwargs)
    def task_estmate_models(
        path_to_data: Path, model: str, path_to_estimation: Annotated[Path, Product]
    ) -> None:
        if model == "linear_probability":
            ...
