from __future__ import annotations

from typing import TYPE_CHECKING

from my_project.config import BLD

if TYPE_CHECKING:
    from pathlib import Path


_DEPENDENCIES = {"data_0": BLD / "data_0.pkl", "data_1": BLD / "data_1.pkl"}
_PRODUCTS = {"plot_0": BLD / "plot_0.png", "plot_1": BLD / "plot_1.png"}


def task_plot_data(
    path_to_data: dict[str, Path] = _DEPENDENCIES,
    produces: dict[str, Path] = _PRODUCTS,
) -> None: ...
