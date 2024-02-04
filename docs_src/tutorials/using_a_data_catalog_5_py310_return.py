from pathlib import Path
from typing import Annotated

import pandas as pd
from my_project.config import data_catalog


def task_transform_csv(
    path: Annotated[Path, data_catalog["csv"]],
) -> Annotated[pd.DataFrame, data_catalog["transformed_csv"]]:
    df = pd.read_csv(path)
    # ... transform the data
    return df
