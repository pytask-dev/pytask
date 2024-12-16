"""Contains implementations of tasks and nodes following the node protocols."""

from __future__ import annotations

import hashlib
import inspect
import pickle
from contextlib import suppress
from os import stat_result
from pathlib import Path  # noqa: TC003
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from attrs import define
from attrs import field
from upath import UPath
from upath._stat import UPathStatResult

from _pytask._hashlib import hash_value
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PProvisionalNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.path import hash_path
from _pytask.typing import NoDefault
from _pytask.typing import no_default

if TYPE_CHECKING:
    from _pytask.mark import Mark
    from _pytask.models import NodeInfo
    from _pytask.tree_util import PyTree


__all__ = [
    "DirectoryNode",
    "PathNode",
    "PickleNode",
    "PythonNode",
    "Task",
    "TaskWithoutPath",
]


@define(kw_only=True)
class TaskWithoutPath(PTask):
    """The class for tasks without a source file.

    Tasks may have no source file because
    - they are dynamically created in a REPL.
    - they are created in a Jupyter notebook.

    Attributes
    ----------
    name
        The name of the task.
    function
        The task function.
    depends_on
        A list of dependencies of task.
    produces
        A list of products of task.
    markers
        A list of markers attached to the task function.
    report_sections
        Reports with entries for when, what, and content.
    attributes: dict[Any, Any]
        A dictionary to store additional information of the task.

    """

    name: str
    function: Callable[..., Any]
    depends_on: dict[str, PyTree[PNode | PProvisionalNode]] = field(factory=dict)
    produces: dict[str, PyTree[PNode | PProvisionalNode]] = field(factory=dict)
    markers: list[Mark] = field(factory=list)
    report_sections: list[tuple[str, str, str]] = field(factory=list)
    attributes: dict[Any, Any] = field(factory=dict)

    @property
    def signature(self) -> str:
        raw_key = str(hash_value(self.name))
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def state(self) -> str | None:
        """Return the state of the node."""
        with suppress(OSError):
            source = inspect.getsource(self.function)
            return hashlib.sha256(source.encode()).hexdigest()
        return None

    def execute(self, **kwargs: Any) -> Any:
        """Execute the task."""
        return self.function(**kwargs)


@define(kw_only=True)
class Task(PTaskWithPath):
    """The class for tasks which are Python functions.

    Attributes
    ----------
    base_name
        The base name of the task.
    path
        Path to the file where the task was defined.
    function
        The task function.
    name
        The name of the task.
    depends_on
        A list of dependencies of task.
    produces
        A list of products of task.
    markers
        A list of markers attached to the task function.
    report_sections
        Reports with entries for when, what, and content.
    attributes: dict[Any, Any]
        A dictionary to store additional information of the task.

    """

    base_name: str
    path: Path
    function: Callable[..., Any]
    name: str = field(default="", init=False)
    depends_on: dict[str, PyTree[PNode | PProvisionalNode]] = field(factory=dict)
    produces: dict[str, PyTree[PNode | PProvisionalNode]] = field(factory=dict)
    markers: list[Mark] = field(factory=list)
    report_sections: list[tuple[str, str, str]] = field(factory=list)
    attributes: dict[Any, Any] = field(factory=dict)

    def __attrs_post_init__(self: Task) -> None:
        """Change class after initialization."""
        if not self.name:
            self.name = self.path.as_posix() + "::" + self.base_name

    @property
    def signature(self) -> str:
        """The unique signature of the node."""
        raw_key = "".join(str(hash_value(arg)) for arg in (self.base_name, self.path))
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def state(self) -> str | None:
        """Return the state of the node."""
        return _get_state(self.path)

    def execute(self, **kwargs: Any) -> Any:
        """Execute the task."""
        return self.function(**kwargs)


@define(kw_only=True)
class PathNode(PPathNode):
    """The class for a node which is a path.

    Attributes
    ----------
    name
        Name of the node which makes it identifiable in the DAG.
    path
        The path to the file.

    """

    path: Path
    name: str = ""

    @property
    def signature(self) -> str:
        """The unique signature of the node."""
        raw_key = str(hash_value(self.path))
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def from_path(cls, path: Path) -> PathNode:
        """Instantiate class from path to file."""
        return cls(name=path.as_posix(), path=path)

    def state(self) -> str | None:
        """Calculate the state of the node.

        The state is given by the modification timestamp.

        """
        return _get_state(self.path)

    def load(self, is_product: bool = False) -> Path:  # noqa: ARG002
        """Load the value."""
        return self.path

    def save(self, value: bytes | str) -> None:
        """Save strings or bytes to file."""
        if isinstance(value, str):
            self.path.write_text(value)
        elif isinstance(value, bytes):
            self.path.write_bytes(value)
        else:
            msg = f"'PathNode' can only save 'str' and 'bytes', not {type(value)}"
            raise TypeError(msg)


@define(kw_only=True)
class PythonNode(PNode):
    """The class for a node which is a Python object.

    Attributes
    ----------
    name
        The name of the node.
    value
        The value of the node.
    hash
        Whether the value should be hashed to determine the state. Use ``True`` for
        objects that are hashable like strings and tuples. For dictionaries and other
        non-hashable objects, you need to provide a function that can hash these
        objects. The function should return either an integer or a string.
    node_info
        The infos acquired while collecting the node.

    Examples
    --------
    To allow a :class:`PythonNode` to hash a dictionary, you need to pass your
    own hashing function. For example, from the :mod:`deepdiff` library.

    >>> from deepdiff import DeepHash
    >>> from pytask import PythonNode
    >>> node = PythonNode(name="node", value={"a": 1}, hash=lambda x: DeepHash(x)[x])

    .. warning:: Hashing big objects can require some time.

    """

    name: str = ""
    value: Any | NoDefault = no_default
    hash: bool | Callable[[Any], int | str] = False
    node_info: NodeInfo | None = None

    @property
    def signature(self) -> str:
        """The unique signature of the node."""
        raw_key = (
            "".join(
                str(hash_value(getattr(self.node_info, name)))
                for name in ("arg_name", "path", "task_name", "task_path")
            )
            if self.node_info
            else str(hash_value(self.node_info))
        )
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def load(self, is_product: bool = False) -> Any:
        """Load the value."""
        if is_product:
            return self
        if isinstance(self.value, PythonNode):
            return self.value.load()
        return self.value

    def save(self, value: Any) -> None:
        """Save the value."""
        self.value = value

    def state(self) -> str | None:
        """Calculate state of the node.

        If ``hash = False``, the function returns ``"0"``, a constant hash value, so the
        :class:`PythonNode` is ignored when checking for a changed state of the task.

        If ``hash`` is a callable, then use this function to calculate a hash expecting
        an integer or string.

        If ``hash = True``, the builtin ``hash()`` function (`link
        <https://docs.python.org/3.11/library/functions.html?highlight=hash#hash>`_) is
        used for all types except strings.

        The hash for strings and bytes is calculated using hashlib because
        ``hash("asd")`` returns a different value every invocation since the hash of
        strings is salted with a random integer and it would confuse users. See
        {meth}`object.__hash__` for more information.

        """
        if self.value is no_default:
            return None
        if self.hash:
            value = self.load()
            if callable(self.hash):
                return str(self.hash(value))
            return str(hash_value(value))
        return "0"


@define
class PickleNode(PPathNode):
    """A node for pickle files.

    Attributes
    ----------
    name
        Name of the node which makes it identifiable in the DAG.
    path
        The path to the file.

    """

    path: Path
    name: str = ""

    @property
    def signature(self) -> str:
        """The unique signature of the node."""
        raw_key = str(hash_value(self.path))
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def from_path(cls, path: Path) -> PickleNode:
        """Instantiate class from path to file."""
        if not path.is_absolute():
            msg = "Node must be instantiated from absolute path."
            raise ValueError(msg)
        return cls(name=path.as_posix(), path=path)

    def state(self) -> str | None:
        return _get_state(self.path)

    def load(self, is_product: bool = False) -> Any:
        if is_product:
            return self
        with self.path.open("rb") as f:
            return pickle.load(f)  # noqa: S301

    def save(self, value: Any) -> None:
        with self.path.open("wb") as f:
            pickle.dump(value, f)


@define(kw_only=True)
class DirectoryNode(PProvisionalNode):
    """The class for a provisional node that works with directories.

    Attributes
    ----------
    name
        The name of the node.
    pattern
        Patterns are the same as for :mod:`fnmatch`, with the addition of ``**`` which
        means "this directory and all subdirectories, recursively".
    root_dir
        The pattern is interpreted relative to the path given by ``root_dir``. If
        ``root_dir = None``, it is the directory where the path is defined.

    """

    name: str = ""
    pattern: str = "*"
    root_dir: Path | None = None

    @property
    def signature(self) -> str:
        """The unique signature of the node."""
        raw_key = "".join(str(hash_value(arg)) for arg in (self.root_dir, self.pattern))
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def load(self, is_product: bool = False) -> Path:
        """Inject a path into the task when loaded as a product."""
        if is_product:
            return self.root_dir  # type: ignore[return-value]
        msg = "'DirectoryNode' cannot be loaded as a dependency"  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover

    def collect(self) -> list[Path]:
        """Collect paths defined by the pattern."""
        return list(self.root_dir.glob(self.pattern))  # type: ignore[union-attr]


def _get_state(path: Path) -> str | None:
    """Get state of a path.

    A simple function to handle local and remote files.

    """
    # Invalidate the cache of the path if it is a UPath because it might have changed in
    # a different process with pytask-parallel and the main process does not know about
    # it and relies on the cache.
    if isinstance(path, UPath):
        path.fs.invalidate_cache()

    try:
        stat = path.stat()
    except FileNotFoundError:
        return None

    if isinstance(stat, stat_result):
        modification_time = stat.st_mtime
        return hash_path(path, modification_time)
    if isinstance(stat, UPathStatResult):
        return stat.as_info().get("ETag", "0")
    msg = "Unknown stat object."
    raise NotImplementedError(msg)
