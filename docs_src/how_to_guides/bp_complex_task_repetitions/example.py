from pathlib import Path
from typing import Annotated

from pytask import Product
from pytask import task

SRC = Path(__file__).parent
BLD = SRC / "bld"


for data_name in ("a", "b", "c"):
    for model_name in ("ols", "logit", "linear_prob"):

        @task(id=f"{model_name}-{data_name}")
        def task_fit_model(
            path_to_data: Path = SRC / f"{data_name}.pkl",
            path_to_model: Annotated[Path, Product] = BLD
            / f"{data_name}-{model_name}.pkl",
        ) -> None: ...
