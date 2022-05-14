# Content of task_module.py
from __future__ import annotations

import shutil
from pathlib import Path

import pytask
from click.testing import CliRunner


def task_example():
    pass


if __name__ == "__main__":
    runner = CliRunner()
    path = Path(__file__).parent

    path.joinpath("obsolete_file_1.md").touch()

    path.joinpath("obsolete_folder").mkdir()
    path.joinpath("obsolete_folder", "obsolete_file_2.md").touch()
    path.joinpath("obsolete_folder", "obsolete_file_3.md").touch()

    pytask.console.record = True
    rs = runner.invoke(pytask.cli, ["clean", "-e", "__pycache__", path.as_posix()])
    pytask.console.save_svg("clean-dry-run.svg", title="pytask")

    pytask.console.record = True
    runner.invoke(pytask.cli, ["clean", "-e", "__pycache__", "-d", path.as_posix()])
    pytask.console.save_svg("clean-dry-run-directories.svg", title="pytask")

    path.joinpath("obsolete_file_1.md").unlink()
    shutil.rmtree(path / "obsolete_folder")
