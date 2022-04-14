from __future__ import annotations

import pytask
from click.testing import CliRunner


def task_first():
    pytask.console.print("I'm second.")


@pytask.mark.try_first
def task_second():
    pytask.console.print("I'm first.")


if __name__ == "__main__":
    runner = CliRunner()

    pytask.console.record = True
    runner.invoke(pytask.cli, [__file__, "--capture=no"])
    pytask.console.save_svg("try-first.svg", title="pytask")
