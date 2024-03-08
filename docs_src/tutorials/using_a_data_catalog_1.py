from pathlib import Path

from pytask import DataCatalog

SRC = Path(__file__).parent.resolve()
BLD = SRC.joinpath("..", "..", "bld").resolve()


data_catalog = DataCatalog()
