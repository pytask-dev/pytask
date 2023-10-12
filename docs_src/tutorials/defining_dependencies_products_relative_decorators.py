from pathlib import Path

import pytask


@pytask.mark.produces("../bld/data.pkl")
def task_create_random_data(produces: Path) -> None:
    ...
