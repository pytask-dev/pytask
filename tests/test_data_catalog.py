from __future__ import annotations

import hashlib
import pickle
import sys
import textwrap
from pathlib import Path

import pytest

from _pytask.data_catalog_utils import DATA_CATALOG_NAME_FIELD
from pytask import DataCatalog
from pytask import ExitCode
from pytask import PathNode
from pytask import PickleNode
from pytask import PythonNode
from pytask import cli

try:
    import pexpect
except ModuleNotFoundError:  # pragma: no cover
    IS_PEXPECT_INSTALLED = False
else:
    IS_PEXPECT_INSTALLED = True


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
    from typing import Annotated

    from pytask import DataCatalog


    # Generate input data
    data_catalog = DataCatalog()
    data_catalog.add("file", Path("file.txt"))
    data_catalog.add("output", Path("output.txt"))


    def task_add_content(
        path: Annotated[Path, data_catalog["file"]]
    ) -> Annotated[str, data_catalog["new_content"]]:
        text = path.read_text()
        text += "World!"
        return text


    def task_save_text(
        text: Annotated[str, data_catalog["new_content"]]
    ) -> Annotated[str, data_catalog["output"]]:
        return text
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("file.txt").write_text("Hello, ")

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("output.txt").read_text() == "Hello, World!"
    assert (
        len(list(tmp_path.joinpath(".pytask", "data_catalogs", "default").iterdir()))
        == 2
    )


def test_use_data_catalog_w_config(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Annotated
    from pytask import DataCatalog

    data_catalog = DataCatalog()

    def task_add_content() -> Annotated[str, data_catalog["new_content"]]:
        return "Hello, World!"
    """
    tmp_path.joinpath("src", "tasks").mkdir(parents=True)
    tmp_path.joinpath("src", "tasks", "task_example.py").write_text(
        textwrap.dedent(source)
    )
    tmp_path.joinpath("pyproject.toml").write_text("[tool.pytask.ini_options]")

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert (
        len(list(tmp_path.joinpath(".pytask", "data_catalogs", "default").iterdir()))
        == 2
    )


def _flush(child):
    if child.isalive():  # pragma: no cover
        child.read()
        child.wait()
    assert not child.isalive()


@pytest.mark.skipif(not IS_PEXPECT_INSTALLED, reason="pexpect is not installed.")
@pytest.mark.skipif(sys.platform == "win32", reason="pexpect cannot spawn on Windows.")
def test_use_data_catalog_in_terminal(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Annotated
    from pytask import DataCatalog

    data_catalog = DataCatalog()

    def task_add_content() -> Annotated[str, data_catalog["new_content"]]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK

    child = pexpect.spawn("python")
    child.sendline(f"import sys; sys.path.insert(0, {tmp_path.as_posix()!r});")
    child.sendline("from task_example import data_catalog;")
    child.sendline("data_catalog.entries;")
    child.sendline("data_catalog['new_content'].load()")
    child.sendline("exit()")
    rest = child.read().decode("utf-8")
    assert "new_content" in rest
    assert "Hello, World!" in rest
    _flush(child)


def test_use_data_catalog_with_different_name(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Annotated
    from pytask import DataCatalog

    data_catalog = DataCatalog(name="blob")

    def task_add_content() -> Annotated[str, data_catalog["new_content"]]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert (
        len(list(tmp_path.joinpath(".pytask", "data_catalogs", "blob").iterdir())) == 2
    )


def test_use_data_catalog_with_different_path(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Annotated
    from pytask import DataCatalog

    data_catalog = DataCatalog(name="blob", path=Path(__file__).parent / ".data")

    def task_add_content() -> Annotated[str, data_catalog["new_content"]]:
        return "Hello, World!"
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert len(list(tmp_path.joinpath(".data").iterdir())) == 2


def test_error_when_name_of_node_is_not_string():
    data_catalog = DataCatalog()
    with pytest.raises(TypeError, match="The name of a catalog entry"):
        data_catalog.add(True, Path("file.txt"))  # type: ignore[arg-type]


def test_requesting_new_node_with_python_node_as_default():
    data_catalog = DataCatalog(default_node=PythonNode)
    assert isinstance(data_catalog["node"], PythonNode)


def test_adding_a_python_node():
    data_catalog = DataCatalog()
    data_catalog.add("node", PythonNode(name="node", value=1))
    assert isinstance(data_catalog["node"], PythonNode)


def test_reloading_data_catalog_preserves_node_attributes(tmp_path):
    data_catalog = DataCatalog(_instance_path=tmp_path)
    _ = data_catalog["node"]
    assert data_catalog.path is not None

    filename = hashlib.sha256(b"node").hexdigest()
    path_to_node = data_catalog.path / f"{filename}-node.pkl"

    node = pickle.loads(path_to_node.read_bytes())  # noqa: S301
    node.attributes["custom"] = "value"
    path_to_node.write_bytes(pickle.dumps(node))

    reloaded_data_catalog = DataCatalog(_instance_path=tmp_path)
    reloaded_node = reloaded_data_catalog["node"]

    assert reloaded_node.attributes["custom"] == "value"
    assert reloaded_node.attributes[DATA_CATALOG_NAME_FIELD] == "default"


def test_use_data_catalog_with_provisional_node(runner, tmp_path):
    source = """
    from pathlib import Path
    from typing import Annotated, List

    from pytask import DataCatalog
    from pytask import DirectoryNode

    # Generate input data
    data_catalog = DataCatalog()
    data_catalog.add("directory", DirectoryNode(pattern="*.txt"))

    def task_add_content(
        paths: Annotated[List[Path], data_catalog["directory"]]
    ) -> Annotated[str, Path("output.txt")]:
        name_to_path = {path.stem: path for path in paths}
        return name_to_path["a"].read_text() + name_to_path["b"].read_text()
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("a.txt").write_text("Hello, ")
    tmp_path.joinpath("b.txt").write_text("World!")

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("output.txt").read_text() == "Hello, World!"


def test_data_catalog_has_invalid_name(runner, tmp_path):
    source = """
    from pytask import DataCatalog

    data_catalog = DataCatalog(name="?1")
    """
    tmp_path.joinpath("task_example.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.COLLECTION_FAILED
    assert "The name of a data catalog" in result.stdout
