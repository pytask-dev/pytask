from __future__ import annotations

import pytask
from click.testing import CliRunner


if __name__ == "__main__":
    runner = CliRunner()

    pytask.console.record = True
    runner.invoke(pytask.cli, ["--help"])
    pytask.console.save_svg("help_page.svg", title="pytask")
