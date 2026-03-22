from pathlib import Path

import numpy as np
import pandas as pd
from my_project.config import BLD


def task_create_random_data(produces: Path = BLD / "data.pkl") -> None:  # (1)!
    rng = np.random.default_rng(0)
    beta = 2

    x = rng.normal(loc=5, scale=10, size=1_000)
    epsilon = rng.standard_normal(1_000)

    y = beta * x + epsilon

    df = pd.DataFrame({"x": x, "y": y})
    df.to_pickle(produces)
