from pathlib import Path

import pandas as pd
from typing_extensions import Annotated

import pytask
from pytask import Product


def _create_df() -> pd.DataFrame:
    df = pd.DataFrame({"a": range(10), "b": range(10, 20)})
    df[df["a"] < 5]["b"] = 1
    return df


@pytask.mark.filterwarnings("ignore:.*:pandas.errors.SettingWithCopyWarning")
def task_warning(path: Annotated[Path, Product] = Path("df.pkl")) -> None:
    df = _create_df()
    df.to_pickle(path)
