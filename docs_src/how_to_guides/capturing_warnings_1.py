from pathlib import Path
from typing import Annotated

import pandas as pd

from pytask import Product


def _create_df() -> pd.DataFrame:
    df = pd.DataFrame({"a": range(10), "b": range(10, 20)})
    df[df["a"] < 5]["b"] = 1
    return df


def task_warning(path: Annotated[Path, Product] = Path("df.pkl")) -> None:
    df = _create_df()
    df.to_pickle(path)
