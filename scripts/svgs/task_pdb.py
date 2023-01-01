# Content of task_data_preparation.py.
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytask
from click.testing import CliRunner


@pytask.mark.produces("data.pkl")
def task_create_random_data(produces: Path) -> None:
    rng = np.random.default_rng(0)
    beta = 2

    x = rng.normal(loc=5, scale=10, size=5)
    epsilon = rng.standard_normal(5)

    y = beta * x + epsilon

    df = pd.DataFrame({"x": x, "y": y})

    raise Exception

    df.to_pickle(produces)


if __name__ == "__main__":
    runner = CliRunner()

    pytask.console.record = True
    runner.invoke(
        pytask.cli,
        [__file__, "--pdb"],
        input="pytask.console.save_svg('pdb.svg', title='pytask')",
    )
