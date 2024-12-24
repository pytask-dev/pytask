import hashlib
import pickle
from pathlib import Path
from typing import Any

from pytask import hash_value


class PickleNode:
    """The class for a node that persists values with pickle to files.

    Parameters
    ----------
    name
        Name of the node which makes it identifiable in the DAG.
    path
        The path to the file.
    attributes
        Additional attributes that are stored in the node.

    """

    def __init__(
        self,
        name: str = "",
        path: Path | None = None,
        attributes: dict[Any, Any] | None = None,
    ) -> None:
        self.name = name
        self.path = path
        self.attributes = attributes or {}

    @property
    def signature(self) -> str:
        """The unique signature of the node."""
        raw_key = str(hash_value(self.path))
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def from_path(cls, path: Path) -> "PickleNode":
        """Instantiate class from path to file."""
        if not path.is_absolute():
            msg = "Node must be instantiated from absolute path."
            raise ValueError(msg)
        return cls(name=path.as_posix(), path=path)

    def state(self) -> str | None:
        """Return the modification timestamp as the state."""
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def load(self, is_product: bool) -> Path:
        """Load the value from the path."""
        if is_product:
            return self
        return pickle.loads(self.path.read_bytes())

    def save(self, value: Any) -> None:
        """Save any value with pickle to the file."""
        self.path.write_bytes(pickle.dumps(value))
