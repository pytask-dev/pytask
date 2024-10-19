from __future__ import annotations

import pickle
import textwrap

import pytest

from pytask import ExitCode
from pytask import cli


@pytest.mark.end_to_end
def test_node_protocol_for_custom_nodes(runner, tmp_path):
    source = """
    from typing import Annotated
    from pytask import Product
    from attrs import define
    from pathlib import Path

    @define
    class CustomNode:
        name: str
        value: str
        signature: str = "id"

        def state(self):
            return self.value

        def load(self, is_product):
            return self.value

        def save(self, value):
            self.value = value

    def task_example(
        data = CustomNode("custom", "text"),
        out: Annotated[Path, Product] = Path("out.txt"),
    ) -> None:
        out.write_text(data)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").read_text() == "text"


@pytest.mark.end_to_end
def test_node_protocol_for_custom_nodes_with_paths(runner, tmp_path):
    source = """
    from typing import Annotated
    from pytask import Product
    from pathlib import Path
    from attrs import define
    import pickle

    @define
    class PickleFile:
        name: str
        path: Path
        value: Path
        signature: str = "id"

        def state(self):
            return str(self.path.stat().st_mtime)

        def load(self, is_product):
            with self.path.open("rb") as f:
                out = pickle.load(f)
            return out

        def save(self, value):
            with self.path.open("wb") as f:
                pickle.dump(value, f)

    _PATH = Path(__file__).parent.joinpath("in.pkl")

    def task_example(
        data = PickleFile(_PATH.as_posix(), _PATH, _PATH),
        out: Annotated[Path, Product] = Path("out.txt"),
    ) -> None:
        out.write_text(data)
    """
    tmp_path.joinpath("task_module.py").write_text(textwrap.dedent(source))
    tmp_path.joinpath("in.pkl").write_bytes(pickle.dumps("text"))

    result = runner.invoke(cli, [tmp_path.as_posix()])
    assert result.exit_code == ExitCode.OK
    assert tmp_path.joinpath("out.txt").read_text() == "text"
