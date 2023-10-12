from pathlib import Path

from typing_extensions import Annotated


def task_create_file() -> Annotated[str, Path("file.txt")]:
    return "This is the content of the text file."
