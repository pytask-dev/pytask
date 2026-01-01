from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cloudpickle


@dataclass
class PickleNode:
    """A node for pickle files.

    Attributes
    ----------
    name
        Name of the node which makes it identifiable in the DAG.
    path
        The path to the file.

    """

    name: str
    path: Path

    @classmethod
    def from_path(cls, path: Path) -> "PickleNode":
        """Instantiate class from path to file."""
        if not path.is_absolute():
            msg = "Node must be instantiated from absolute path."
            raise ValueError(msg)
        return cls(name=path.as_posix(), path=path)

    def state(self) -> str | None:
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def load(self, is_product: bool = False) -> Any:
        if is_product:
            return self
        with self.path.open("rb") as f:
            return cloudpickle.load(f)

    def save(self, value: Any) -> None:
        with self.path.open("wb") as f:
            cloudpickle.dump(value, f)
