# Content of task_data_management.py
from pathlib import Path
from typing import Annotated

import pandas as pd

from pytask import Product


def task_prepare_data(
    path_to_csv: Path = Path("data.csv"),
    path_to_pkl: Annotated[Path, Product] = Path("data.pkl"),
) -> None:
    df = pd.read_csv(path_to_csv)

    # Many operations.

    df.to_pickle(path_to_pkl)
