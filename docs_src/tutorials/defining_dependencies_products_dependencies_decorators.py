from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pytask
from my_project.config import BLD


@pytask.mark.depends_on(BLD / "data.pkl")
@pytask.mark.produces(BLD / "plot.png")
def task_plot_data(depends_on: Path, produces: Path) -> None:
    df = pd.read_pickle(depends_on)

    _, ax = plt.subplots()
    df.plot(x="x", y="y", ax=ax, kind="scatter")

    plt.savefig(produces)
    plt.close()
