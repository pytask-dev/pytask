from pathlib import Path

from pytask import DataCatalog


SRC = Path(__file__).parent.resolve()
BLD = SRC.joinpath("..", "..", "bld").resolve()


data_catalog = DataCatalog()

# Use either a relative or a absolute path.
data_catalog.add("csv", Path("file.csv"))
data_catalog.add("transformed_csv", BLD / "file.pkl")
