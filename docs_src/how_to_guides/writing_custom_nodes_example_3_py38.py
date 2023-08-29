import pickle
from pathlib import Path
from typing import Any
from typing import Optional


class PickleNode:
    """The class for a node that persists values with pickle to files.

    Parameters
    ----------
    name
        Name of the node which makes it identifiable in the DAG.
    value
        Value which can be requested inside the function.
    path
        The path to the file.

    """

    def __init__(
        self, name: str = "", value: Optional[Path] = None, path: Optional[Path] = None
    ) -> None:
        self.name = name
        self.value = value
        self.path = path

    def from_annot(self, value: Path) -> None:
        """Set path and if other attributes are not set, set sensible defaults."""
        if not isinstance(value, Path):
            raise TypeError("'value' must be a 'pathlib.Path'.")
        if not self.name:
            self.name = value.as_posix()
        self.value = value

    @classmethod
    def from_path(cls, path: Path) -> "PickleNode":
        """Instantiate class from path to file."""
        if not path.is_absolute():
            raise ValueError("Node must be instantiated from absolute path.")
        return cls(name=path.as_posix(), value=path, path=path)

    def state(self) -> Optional[str]:
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
