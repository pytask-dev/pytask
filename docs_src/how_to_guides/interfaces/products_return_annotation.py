from pathlib import Path
from typing import Annotated


def task_write_file() -> Annotated[str, Path("file.txt")]:
    return ""
