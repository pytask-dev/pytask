from pathlib import Path
from typing import Dict

from my_project.config import BLD

_PRODUCTS = {"first": BLD / "data_0.pkl", "second": BLD / "data_1.pkl"}


def task_plot_data(
    path_to_data_0: Path = BLD / "data_0.pkl",
    path_to_data_1: Path = BLD / "data_1.pkl",
    produces: Dict[str, Path] = _PRODUCTS,
) -> None: ...
