from pathlib import Path

from my_project.config import BLD
from pytask import Product
from typing_extensions import Annotated


_DEPENDENCIES = {"data_0": BLD / "data_0.pkl", "data_1": BLD / "data_1.pkl"}
_PRODUCTS = {"plot_0": BLD / "plot_0.png", "plot_1": BLD / "plot_1.png"}


def task_plot_data(
    path_to_data: dict[str, Path] = _DEPENDENCIES,
    path_to_plots: Annotated[dict[str, Path], Product] = _PRODUCTS,
) -> None:
    ...
