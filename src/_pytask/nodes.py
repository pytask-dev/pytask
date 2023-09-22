"""Contains implementations of tasks and nodes following the node protocols."""
from __future__ import annotations

import functools
import hashlib
import inspect
from pathlib import Path  # noqa: TCH003
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from attrs import define
from attrs import field


if TYPE_CHECKING:
    from _pytask.tree_util import PyTree
    from _pytask.mark import Mark


__all__ = ["PathNode", "PythonNode", "Task", "TaskWithoutPath"]


@define(kw_only=True)
class TaskWithoutPath(PTask):
    """The class for tasks without a source file.

    Tasks may have no source file because
    - they are dynamically created in a REPL.
    - they are created in a Jupyter notebook.

    """

    name: str
    """The base name of the task."""
    function: Callable[..., Any]
    """The task function."""
    depends_on: PyTree[PNode] = field(factory=dict)
    """A list of dependencies of task."""
    produces: PyTree[PNode] = field(factory=dict)
    """A list of products of task."""
    markers: list[Mark] = field(factory=list)
    """A list of markers attached to the task function."""
    report_sections: list[tuple[str, str, str]] = field(factory=list)
    """Reports with entries for when, what, and content."""
    attributes: dict[Any, Any] = field(factory=dict)
    """A dictionary to store additional information of the task."""

    def state(self) -> str | None:
        """Return the state of the node."""
        try:
            source = inspect.getsource(self.function)
        except OSError:
            return None
        else:
            return hashlib.sha256(source.encode()).hexdigest()

    def execute(self, **kwargs: Any) -> None:
        """Execute the task."""
        return self.function(**kwargs)


@define(kw_only=True)
class Task(PTaskWithPath):
    """The class for tasks which are Python functions."""

    base_name: str
    """The base name of the task."""
    path: Path | None
    """Path to the file where the task was defined."""
    function: Callable[..., Any]
    """The task function."""
    name: str | None = field(default=None, init=False)
    """The name of the task."""
    display_name: str | None = field(default=None, init=False)
    """The shortest uniquely identifiable name for task for display."""
    depends_on: PyTree[PNode] = field(factory=dict)
    """A list of dependencies of task."""
    produces: PyTree[PNode] = field(factory=dict)
    """A list of products of task."""
    markers: list[Mark] = field(factory=list)
    """A list of markers attached to the task function."""
    report_sections: list[tuple[str, str, str]] = field(factory=list)
    """Reports with entries for when, what, and content."""
    attributes: dict[Any, Any] = field(factory=dict)
    """A dictionary to store additional information of the task."""

    def __attrs_post_init__(self: Task) -> None:
        """Change class after initialization."""
        if self.name is None:
            if self.path is None:
                self.name = self.base_name
            else:
                self.name = self.path.as_posix() + "::" + self.base_name

        if self.display_name is None:
            self.display_name = self.name

    def state(self) -> str | None:
        """Return the state of the node."""
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def execute(self, **kwargs: Any) -> None:
        """Execute the task."""
        return self.function(**kwargs)


@define(kw_only=True)
class PathNode(PPathNode):
    """The class for a node which is a path."""

    name: str
    """Name of the node which makes it identifiable in the DAG."""
    path: Path
    """The path to the file."""

    @classmethod
    @functools.lru_cache
    def from_path(cls, path: Path) -> PathNode:
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            msg = "Node must be instantiated from absolute path."
            raise ValueError(msg)
        return cls(name=path.as_posix(), path=path)

    def state(self) -> str | None:
        """Calculate the state of the node.

        The state is given by the modification timestamp.

        """
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def load(self) -> Path:
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
    """The class for a node which is a Python object."""

    name: str = ""
    """Name of the node."""
    value: Any = None
    """Value of the node."""
    hash: bool | Callable[[Any], bool] = False  # noqa: A003
    """Whether the value should be hashed to determine the state."""

    def load(self) -> Any:
        """Load the value."""
        return self.value

    def save(self, value: Any) -> None:
        """Save the value."""
        self.value = value

    def state(self) -> str | None:
        """Calculate state of the node.

        If ``hash = False``, the function returns ``"0"``, a constant hash value, so the
        :class:`PythonNode` is ignored when checking for a changed state of the task.

        If ``hash`` is a callable, then use this function to calculate a hash.

        If ``hash = True``, the builtin ``hash()`` function (`link
        <https://docs.python.org/3.11/library/functions.html?highlight=hash#hash>`_) is
        used for all types except strings.

        The hash for strings and bytes is calculated using hashlib because
        ``hash("asd")`` returns a different value every invocation since the hash of
        strings is salted with a random integer and it would confuse users. See
        {meth}`object.__hash__` for more information.

        """
        if self.hash:
            if callable(self.hash):
                return str(self.hash(self.value))
            if isinstance(self.value, str):
                return str(hashlib.sha256(self.value.encode()).hexdigest())
            if isinstance(self.value, bytes):
                return str(hashlib.sha256(self.value).hexdigest())
            return str(hash(self.value))
        return "0"
