# Content of task_prepare_data.py
from pathlib import Path

from my_project.data_preparation.config import DATA
from my_project.data_preparation.config import path_to_input_data
from my_project.data_preparation.config import path_to_processed_data
from pytask import Product
from pytask import task
from typing_extensions import Annotated


def _create_parametrization(data: list[str]) -> dict[str, Path]:
    id_to_kwargs = {}
    for data_name in data:
        id_to_kwargs[data_name] = {
            "path_to_input_data": path_to_input_data(data_name),
            "path_to_processed_data": path_to_processed_data(data_name),
        }

    return id_to_kwargs


_ID_TO_KWARGS = _create_parametrization(DATA)


for id_, kwargs in _ID_TO_KWARGS.items():

    @task(id=id_, kwargs=kwargs)
    def task_prepare_data(
        path_to_input_data: Path, path_to_processed_data: Annotated[Path, Product]
    ) -> None:
        ...
