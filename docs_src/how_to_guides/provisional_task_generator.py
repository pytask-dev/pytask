from pathlib import Path

from typing_extensions import Annotated

from pytask import DirectoryNode
from pytask import task


@task(is_generator=True)
def task_copy_files(
    paths: Annotated[
        list[Path], DirectoryNode(root_dir=Path("downloads"), pattern="*")
    ],
) -> None:
    """Create tasks to copy each file to a ``.txt`` file."""
    for path in paths:
        # The path of the copy will be CITATION.txt, for example.
        path_to_copy = path.with_suffix(".txt")

        @task
        def copy_file(path: Annotated[Path, path]) -> Annotated[str, path_to_copy]:
            return path.read_text()
