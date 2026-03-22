from dataclasses import dataclass
from pathlib import Path

from pytask import DataCatalog

SRC = Path(__file__).parent
BLD = SRC / "bld"

data_catalog = DataCatalog()


@dataclass
class Dataset:
    name: str

    @property
    def path(self) -> Path:
        return SRC / f"{self.name}.pkl"


@dataclass
class Model:
    name: str


DATASETS = [Dataset("a"), Dataset("b"), Dataset("c")]
MODELS = [Model("ols"), Model("logit"), Model("linear_prob")]


@dataclass
class Experiment:
    dataset: Dataset
    model: Model

    @property
    def name(self) -> str:
        return f"{self.model.name}-{self.dataset.name}"

    @property
    def fitted_model_name(self) -> str:
        return f"{self.name}-fitted-model"


EXPERIMENTS = [Experiment(dataset, model) for dataset in DATASETS for model in MODELS]
