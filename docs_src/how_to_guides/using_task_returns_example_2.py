from pathlib import Path

import pytask


func = lambda *x: "This is the content of the text file."


task_create_file = pytask.mark.task(produces=Path("file.txt"))(func)
