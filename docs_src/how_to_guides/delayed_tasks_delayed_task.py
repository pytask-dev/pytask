from pathlib import Path

from pytask import DelayedPathNode
from typing_extensions import Annotated


def task_merge_files(
    paths: Annotated[
        list[Path], DelayedPathNode(root_dir=Path("downloads"), pattern="*")
    ],
) -> Annotated[str, Path("all_text.txt")]:
    """Merge files."""
    contents = [path.read_text() for path in paths]
    return "\n".join(contents)
