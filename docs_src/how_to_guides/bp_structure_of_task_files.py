from pathlib import Path

import pandas as pd
from checks import perform_general_checks_on_data
from pytask import Product
from typing_extensions import Annotated


def task_prepare_census_data(
    path_to_raw_census: Path = Path("raw_census.csv"),
    path_to_census: Annotated[Path, Product] = Path("census.pkl"),
) -> None:
    """Prepare the census data.

    This task prepares the data in three steps.

    1. Clean the data.
    2. Create new variables.
    3. Perform some checks on the new data.

    """
    df = pd.read_csv(path_to_raw_census)

    df = _clean_data(df)

    df = _create_new_variables(df)

    perform_general_checks_on_data(df)

    df.to_pickle(path_to_census)


def _clean_data(df: pd.DataFrame) -> None:
    ...


def _create_new_variables(df: pd.DataFrame) -> None:
    ...
