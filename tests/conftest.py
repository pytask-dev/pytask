from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def _add_objects_to_doctest_namespace(doctest_namespace):
    doctest_namespace["Path"] = Path
