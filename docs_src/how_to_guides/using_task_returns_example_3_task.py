from pathlib import Path

from pytask import task

func = lambda *x: "This is the first content.", "This is the second content."


task_create_file = task(produces=(Path("file1.txt"), Path("file2.txt")))(func)
