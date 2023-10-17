from __future__ import annotations

import textwrap
from pathlib import Path

from pytask import cli
from pytask import DataCatalog
from pytask import ExitCode
from pytask import PathNode
from pytask import PickleNode
from pytask import PythonNode


def test_data_catalog_knows_path_where_it_is_defined():
    data_catalog = DataCatalog()
    assert Path(__file__).parent == data_catalog._instance_path


def test_data_catalog_collects_nodes():
    data_catalog = DataCatalog()

    default_node = data_catalog["default_node"]
    assert isinstance(default_node, PickleNode)

    data_catalog.add("node", Path("file.txt"))
    assert isinstance(data_catalog["node"], PathNode)


def test_change_default_node():
    data_catalog = DataCatalog(default_node=PythonNode)
    default_node = data_catalog["new_default_node"]
    assert isinstance(default_node, PythonNode)


def test_use_data_catalog_in_workflow(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing_extensions import Annotated

    from pytask import DataCatalog


    # Generate input data
    _DataCatalog = DataCatalog()
    _DataCatalog.add("file", Path("file.txt"))
    _DataCatalog.add("output", Path("output.txt"))


    def task_add_content(
        path: Annotated[Path, _DataCatalog["file"]]
    ) -> Annotated[str, _DataCatalog["new_content"]]:
        text = path.read_text()
        text += "World!"
        return text


    def task_save_text(
        text: Annotated[str, _DataCatalog["new_content"]]
    ) -> Annotated[str, _DataCatalog["output"]]:
        return text
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("file.txt").write_text("Hello, ")

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("output.txt").read_text() == "Hello, World!"
