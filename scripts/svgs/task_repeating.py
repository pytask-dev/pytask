from __future__ import annotations

from pathlib import Path

import pytask
from click.testing import CliRunner


for i in range(10):

    @pytask.mark.task
    def task_create_random_data(produces=f"data_{i}.pkl", seed=i):  # noqa: U100
        produces.write_text(seed)


if __name__ == "__main__":
    runner = CliRunner()

    pytask.console.record = True
    runner.invoke(pytask.cli, [__file__])
    pytask.console.save_svg("repeating.svg", title="pytask")

    for i in range(10):
        Path(__file__).parent.joinpath(f"data_{i}.pkl").unlink()
