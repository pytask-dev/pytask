from __future__ import annotations

import pickle
import textwrap

from pytask import ExitCode
from pytask import cli


def test_node_protocol_for_custom_nodes(runner, tmp_path):
    source = """
    from typing import Annotated
    from typing import Any
    from pytask import Product
    from dataclasses import dataclass
    from dataclasses import field
    from pathlib import Path

    @dataclass
    class CustomNode:
        name: str
        value: str
        signature: str = "id"
        attributes: dict[Any, Any] = field(default_factory=dict)

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
    assert "FutureWarning" not in result.output


def test_node_protocol_for_custom_nodes_with_paths(runner, tmp_path):
    source = """
    from typing import Annotated
    from typing import Any
    from pytask import Product
    from pathlib import Path
    from dataclasses import dataclass
    from dataclasses import field
    import pickle

    @dataclass
    class PickleFile:
        name: str
        path: Path
        value: Path
        signature: str = "id"
        attributes: dict[Any, Any] = field(default_factory=dict)

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


def test_node_protocol_for_custom_nodes_adding_attributes(runner, tmp_path):
    source = """
    from typing import Annotated
    from pytask import Product
    from dataclasses import dataclass
    from pathlib import Path

    @dataclass
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
    assert "FutureWarning" in result.output
