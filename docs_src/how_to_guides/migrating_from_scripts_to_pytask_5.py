from pathlib import Path
from typing import Optional

import pandas as pd
from pytask import Product
from typing_extensions import Annotated


def task_merge_data(
    paths_to_input_data: Optional[dict[str, Path]] = None,
    path_to_merged_data: Annotated[Path, Product] = Path("merged_data.pkl"),
) -> None:
    if paths_to_input_data is None:
        paths_to_input_data = {
            "first": Path("data_1.csv"),
            "second": Path("data_2.csv"),
        }
    df1 = pd.read_csv(paths_to_input_data["first"])
    df2 = pd.read_csv(paths_to_input_data["second"])

    df = df1.merge(df2, on=...)

    df.to_pickle(path_to_merged_data)
