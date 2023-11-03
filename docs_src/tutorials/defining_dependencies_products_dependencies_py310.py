from pathlib import Path
from typing import Annotated

import matplotlib.pyplot as plt
import pandas as pd
from my_project.config import BLD
from pytask import Product


def task_plot_data(
    path_to_data: Path = BLD / "data.pkl",
    path_to_plot: Annotated[Path, Product] = BLD / "plot.png",
) -> None:
    df = pd.read_pickle(path_to_data)

    _, ax = plt.subplots()
    df.plot(x="x", y="y", ax=ax, kind="scatter")

    plt.savefig(path_to_plot)
    plt.close()
