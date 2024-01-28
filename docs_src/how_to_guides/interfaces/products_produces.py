from pathlib import Path


def task_write_file(produces: Path = Path("file.txt")) -> None:
    produces.touch()
