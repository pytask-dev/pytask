from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytask
from click.testing import CliRunner


def _create_df() -> pd.DataFrame:
    df = pd.DataFrame({"a": range(10), "b": range(10, 20)})
    df[df["a"] < 5]["b"] = 1  # noqa: PLR2004
    return df


@pytask.mark.produces("df.pkl")
def task_warning(produces: Path) -> None:
    df = _create_df()
    df.to_pickle(produces)


if __name__ == "__main__":
    runner = CliRunner()

    path = Path(__file__).parent

    pytask.console.record = True
    runner.invoke(pytask.cli, [__file__])
    pytask.console.save_svg("warning.svg", title="pytask")

    path.joinpath("df.pkl").unlink()
