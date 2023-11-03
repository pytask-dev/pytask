import numpy as np
import pandas as pd
from my_project.config import data_catalog
from my_project.config import PickleNode


def task_create_random_data(produces: PickleNode = data_catalog["data"]) -> None:
    rng = np.random.default_rng(0)
    beta = 2

    x = rng.normal(loc=5, scale=10, size=1_000)
    epsilon = rng.standard_normal(1_000)

    y = beta * x + epsilon

    df = pd.DataFrame({"x": x, "y": y})
    produces.save(df)
