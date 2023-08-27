from pathlib import Path

import pytask


func = lambda *x: "This is the first content.", "This is the second content."


task_create_file = pytask.mark.task(produces=(Path("file1.txt"), Path("file2.txt")))(
    func
)
