from pathlib import Path
import pytask


@pytask.mark.task(produces=Path("file.txt"))
def task_create_file() -> str:
    return "This is the content of the text file."
