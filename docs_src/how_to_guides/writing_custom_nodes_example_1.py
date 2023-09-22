from pathlib import Path

import pandas as pd


def task_example(in_: Path = Path("in.pkl"), out: Path = Path("out.pkl")) -> None:
    df = pd.read_pickle(in_.read_bytes())
    # Some transformations.
    df.to_pickle(out)
