from pathlib import Path

from pytask import task


@task(kwargs={"path": Path("input.txt")})
def task_example(path: Path) -> None: ...
