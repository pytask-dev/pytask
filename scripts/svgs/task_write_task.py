# Content of task_data_preparation.py.
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytask


@pytask.mark.produces("data.pkl")
def task_create_random_data(produces):
    rng = np.random.default_rng(0)
    beta = 2

    x = rng.normal(loc=5, scale=10, size=1_000)
    epsilon = rng.standard_normal(1_000)

    y = beta * x + epsilon

    df = pd.DataFrame({"x": x, "y": y})
    df.to_pickle(produces)


if __name__ == "__main__":
    pytask.console.record = True
    pytask.main({"paths": __file__})
    pytask.console.save_svg("write-a-task.svg", title="pytask")

    Path(__file__).parent.joinpath("data.pkl").unlink()
