from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from my_project.config import BLD
from my_project.config import data_catalog
from typing_extensions import Annotated

from pytask import Product


def task_plot_data(
    df: Annotated[pd.DataFrame, data_catalog["data"]],
    path_to_plot: Annotated[Path, Product] = BLD / "plot.png",
) -> None:
    _, ax = plt.subplots()
    df.plot(x="x", y="y", ax=ax, kind="scatter")

    plt.savefig(path_to_plot)
    plt.close()
