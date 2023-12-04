from pathlib import Path

from pytask import task


@task(produces=Path("file.txt"))
def task_write_file() -> str:
    return ""
