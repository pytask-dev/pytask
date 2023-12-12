from pathlib import Path
from typing import Annotated

from upath import UPath


url = UPath("https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data")


def task_download_file(path: UPath = url) -> Annotated[str, Path("data.csv")]:
    return path.read_text()
