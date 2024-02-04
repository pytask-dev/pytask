from pathlib import Path

import pandas as pd
from my_project.config import data_catalog
from pytask import PickleNode
from pytask import Product
from typing_extensions import Annotated


def task_transform_csv(
    path: Annotated[Path, data_catalog["csv"]],
    node: Annotated[PickleNode, Product] = data_catalog["transformed_csv"],
) -> None:
    df = pd.read_csv(path)
    # ... transform the data
    node.save(df)
