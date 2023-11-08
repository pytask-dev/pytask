from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from my_project.config import BLD


def task_plot_data(
    path_to_data: Path = BLD / "data.pkl", produces: Path = BLD / "plot.png"
) -> None:
    df = pd.read_pickle(path_to_data)

    _, ax = plt.subplots()
    df.plot(x="x", y="y", ax=ax, kind="scatter")

    plt.savefig(produces)
    plt.close()
