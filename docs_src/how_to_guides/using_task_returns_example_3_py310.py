from pathlib import Path
from typing import Annotated


def task_create_files() -> Annotated[str, (Path("file1.txt"), Path("file2.txt"))]:
    return "This is the first content.", "This is the second content."
