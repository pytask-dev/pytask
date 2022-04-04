# Content of task_module.py
from __future__ import annotations

from pathlib import Path

import pytask
from click.testing import CliRunner


@pytask.mark.depends_on("in.txt")
@pytask.mark.produces("out.txt")
def task_write_file(depends_on, produces):
    produces.write_text(depends_on.read_text())


if __name__ == "__main__":
    runner = CliRunner()
    path = Path(__file__)
    path.parent.joinpath("in.txt").touch()

    pytask.console.record = True
    runner.invoke(pytask.cli, ["collect", path.as_posix()])
    pytask.console.save_svg("collect.svg", title="pytask")

    runner.invoke(pytask.cli, ["collect", "--nodes", path.as_posix()])
    pytask.console.save_svg("collect-nodes.svg", title="pytask")

    path.parent.joinpath("in.txt").unlink()
