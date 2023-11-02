from pathlib import Path
from typing import Annotated

import pandas as pd
from my_project.config import data_catalog
from pytask import PickleNode
from pytask import Product


def task_transform_csv(
    path: Annotated[Path, data_catalog["csv"]],
    node: Annotated[PickleNode, Product] = data_catalog["transformed_csv"],
) -> None:
    df = pd.read_csv(path)
    ...
    node.save(df)
