from pathlib import Path

import pandas as pd
from typing_extensions import Annotated


class PickleNode:
    ...


in_node = PickleNode.from_path(Path(__file__).parent / "in.pkl")
out_node = PickleNode.from_path(Path(__file__).parent / "out.pkl")


def task_example(
    df: Annotated[pd.DataFrame, in_node]
) -> Annotated[pd.DataFrame, out_node]:
    return df.apply(...)
