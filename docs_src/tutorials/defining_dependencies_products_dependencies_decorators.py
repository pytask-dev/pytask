from pathlib import Path

import pytask
from my_project.config import BLD


@pytask.mark.depends_on(BLD / "data.pkl")
@pytask.mark.produces(BLD / "plot.png")
def task_plot_data(depends_on: Path, produces: Path) -> None:
    ...
