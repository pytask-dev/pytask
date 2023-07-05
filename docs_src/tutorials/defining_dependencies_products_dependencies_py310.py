from pathlib import Path
from typing import Annotated

from my_project.config import BLD
from pytask import Product


def task_plot_data(
    path_to_data: Path = BLD / "data.pkl",
    path_to_plot: Annotated[Path, Product] = BLD / "plot.png",
) -> None:
    ...
