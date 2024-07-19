from pathlib import Path
from typing import NamedTuple

from pytask import DataCatalog

SRC = Path(__file__).parent
BLD = SRC / "bld"

data_catalog = DataCatalog()


class Dataset(NamedTuple):
    name: str

    @property
    def path(self) -> Path:
        return SRC / f"{self.name}.pkl"


class Model(NamedTuple):
    name: str


DATASETS = [Dataset("a"), Dataset("b"), Dataset("c")]
MODELS = [Model("ols"), Model("logit"), Model("linear_prob")]


class Experiment(NamedTuple):
    dataset: Dataset
    model: Model

    @property
    def name(self) -> str:
        return f"{self.model.name}-{self.dataset.name}"

    @property
    def fitted_model_name(self) -> str:
        return f"{self.name}-fitted-model"


EXPERIMENTS = [Experiment(dataset, model) for dataset in DATASETS for model in MODELS]
