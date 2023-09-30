# Content of task_module.py
from pathlib import Path


def task_write_file(
    input_path: Path = Path("in.txt"), output_path: Path = Path("out.txt")
) -> None:
    output_path.write_text(input_path.read_text())
