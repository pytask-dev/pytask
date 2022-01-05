import subprocess

import pytest
from pytask import __version__


@pytest.mark.end_to_end
def test_version_option():
    process = subprocess.run(["pytask", "--version"], capture_output=True)
    assert "pytask, version " + __version__ in process.stdout.decode("utf-8")
