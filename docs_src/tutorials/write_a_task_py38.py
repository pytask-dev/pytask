# Content of task_data_preparation.py.
from pathlib import Path

import numpy as np
import pandas as pd
from my_project.config import BLD
from pytask import Product
from typing_extensions import Annotated


def task_create_random_data(path: Annotated[Path, Product] = BLD / "data.pkl") -> None:
    rng = np.random.default_rng(0)
    beta = 2

    x = rng.normal(loc=5, scale=10, size=1_000)
    epsilon = rng.standard_normal(1_000)

    y = beta * x + epsilon

    df = pd.DataFrame({"x": x, "y": y})
    df.to_pickle(path)
