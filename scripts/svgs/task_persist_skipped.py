# Content of task_module.py
from __future__ import annotations

from pathlib import Path

import pytask
from click.testing import CliRunner


@pytask.mark.persist
@pytask.mark.depends_on("input.md")
@pytask.mark.produces("output.md")
def task_make_input_bold(depends_on, produces):
    produces.write_text("**" + depends_on.read_text() + "**")


if __name__ == "__main__":
    runner = CliRunner()
    path = Path(__file__)

    path.parent.joinpath("input.md").touch()
    runner.invoke(pytask.cli, [path.as_posix()])
    runner.invoke(pytask.cli, [path.as_posix()])

    pytask.console.record = True
    runner.invoke(pytask.cli, [path.as_posix(), "--verbose", 2])
    pytask.console.save_svg("persist-skipped.svg", title="pytask")

    path.parent.joinpath("input.md").unlink()
    path.parent.joinpath("output.md").unlink()
