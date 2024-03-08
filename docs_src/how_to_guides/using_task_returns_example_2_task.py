from pathlib import Path

from pytask import task

func = lambda *x: "This is the content of the text file."


task_create_file = task(produces=Path("file.txt"))(func)
