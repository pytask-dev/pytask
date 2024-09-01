from pathlib import Path

import pandas as pd
from typing_extensions import Annotated

from pytask import Product


class PickleNode: ...


in_node = PickleNode.from_path(Path(__file__).parent / "in.pkl")
out_node = PickleNode.from_path(Path(__file__).parent / "out.pkl")


def task_example(
    df: Annotated[pd.DataFrame, in_node], out: Annotated[PickleNode, out_node, Product]
) -> None:
    transformed = df.apply(...)
    out.save(transformed)
