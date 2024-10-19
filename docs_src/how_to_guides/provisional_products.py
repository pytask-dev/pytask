from pathlib import Path
from typing import Annotated

import httpx

from pytask import DirectoryNode
from pytask import Product


def get_files_without_file_extensions_from_repo() -> list[str]:
    url = "https://api.github.com/repos/pytask-dev/pytask/git/trees/main"
    response = httpx.get(url, timeout=10)
    elements = response.json()["tree"]
    return [
        e["path"]
        for e in elements
        if e["type"] == "blob" and Path(e["path"]).suffix == ""
    ]


def task_download_files(
    download_folder: Annotated[
        Path, DirectoryNode(root_dir=Path("downloads"), pattern="*"), Product
    ],
) -> None:
    """Download files."""
    # Contains names like CITATION or LICENSE.
    files_to_download = get_files_without_file_extensions_from_repo()

    for file_ in files_to_download:
        url = "raw.githubusercontent.com/pytask-dev/pytask/main"
        response = httpx.get(url=f"{url}/{file_}", timeout=5)
        content = response.text
        download_folder.joinpath(file_).write_text(content)
