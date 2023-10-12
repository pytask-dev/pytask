# Content of task_data_management.py
from pathlib import Path

import pytask


@pytask.mark.r(script="prepare_data.r")
def task_prepare_data(
    input_path: Path = Path("data.csv"), output_path: Path = Path("data.rds")
) -> None:
    pass
