import pickle
from pathlib import Path
from typing import Any


class PickleNode:
    """The class for a node that persists values with pickle to files.

    Parameters
    ----------
    name
        Name of the node which makes it identifiable in the DAG.
    path
        The path to the file.

    """

    def __init__(self, name: str = "", path: Path | None = None) -> None:
        self.name = name
        self.path = path

    @classmethod
    def from_path(cls, path: Path) -> "PickleNode":
        """Instantiate class from path to file."""
        if not path.is_absolute():
            raise ValueError("Node must be instantiated from absolute path.")
        return cls(name=path.as_posix(), path=path)

    def state(self) -> str | None:
        """Return the modification timestamp as the state."""
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def load(self) -> Path:
        """Load the value from the path."""
        return pickle.loads(self.path.read_bytes())

    def save(self, value: Any) -> None:
        """Save any value with pickle to the file."""
        self.path.write_bytes(pickle.dumps(value))
