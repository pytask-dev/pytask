from pathlib import Path
from typing import Annotated

from my_project.config import BLD
from pytask import Product


def task_plot_data(
    path_to_data_0: Path = BLD / "data_0.pkl",
    path_to_data_1: Path = BLD / "data_1.pkl",
    path_to_plot_0: Annotated[Path, Product] = BLD / "plot_0.png",
    path_to_plot_1: Annotated[Path, Product] = BLD / "plot_1.png",
) -> None:
    ...
