from __future__ import annotations

import pytask
from click.testing import CliRunner


if __name__ == "__main__":
    runner = CliRunner()

    pytask.console.record = True
    runner.invoke(pytask.cli, ["profile"])
    pytask.console.save_svg("profile.svg", title="pytask")
