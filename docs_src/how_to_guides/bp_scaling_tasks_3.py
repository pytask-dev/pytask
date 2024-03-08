# Content of config.py
from pathlib import Path

from my_project.config import BLD
from my_project.data_preparation.config import DATA

_MODELS = ["linear_probability", "logistic_model", "decision_tree"]


ESTIMATIONS = {
    f"{data_name}_{model_name}": {"model": model_name, "data": data_name}
    for model_name in _MODELS
    for data_name in DATA
}


def path_to_estimation_result(name: str) -> Path:
    return BLD / "estimation" / f"estimation_{name}.pkl"
