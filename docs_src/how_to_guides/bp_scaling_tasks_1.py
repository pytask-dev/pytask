# Content of config.py
from pathlib import Path

from my_project.config import BLD
from my_project.config import SRC


DATA = {
    "data_0": {"subset": "subset_1"},
    "data_1": {"subset": "subset_2"},
    "data_2": {"subset": "subset_3"},
    "data_3": {"subset": "subset_4"},
}


def path_to_input_data(name: str) -> Path:
    return SRC / "data" / "data.csv"


def path_to_processed_data(name: str) -> Path:
    return BLD / "data" / f"processed_{name}.pkl"
