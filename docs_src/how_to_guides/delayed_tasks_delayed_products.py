from pathlib import Path

import requests
from pytask import DelayedPathNode
from pytask import Product
from typing_extensions import Annotated


def task_download_files(
    download_folder: Annotated[
        Path, DelayedPathNode(root_dir=Path("downloads"), pattern="*"), Product
    ],
) -> None:
    """Download files."""
    # Scrape list of files without file extension from
    # https://github.com/pytask-dev/pytask. (We skip this part for simplicity.)
    files_to_download = ("CITATION", "LICENSE")

    # Download them.
    for file_ in files_to_download:
        response = requests.get(
            url=f"raw.githubusercontent.com/pytask-dev/pytask/main/{file_}", timeout=5
        )
        content = response.text
        download_folder.joinpath(file_).write_text(content)
