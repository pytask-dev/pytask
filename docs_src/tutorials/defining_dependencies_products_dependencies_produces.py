from pathlib import Path

from my_project.config import BLD


def task_plot_data(
    path_to_data: Path = BLD / "data.pkl", produces: Path = BLD / "plot.png"
) -> None:
    ...
