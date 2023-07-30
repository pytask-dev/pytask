"""Deals with nodes which are dependencies or products of a task."""
from __future__ import annotations

import functools
import hashlib
from pathlib import Path
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

from _pytask.node_protocols import MetaNode
from _pytask.node_protocols import Node
from _pytask.tree_util import PyTree
from attrs import define
from attrs import field


if TYPE_CHECKING:
    from _pytask.mark import Mark


__all__ = ["PathNode", "Product", "Task"]


@define(frozen=True)
class ProductType:
    """A class to mark products."""


Product = ProductType()


@define(kw_only=True)
class Task(MetaNode):
    """The class for tasks which are Python functions."""

    base_name: str
    """The base name of the task."""
    path: Path
    """Path to the file where the task was defined."""
    function: Callable[..., Any]
    """The task function."""
    name: str | None = field(default=None, init=False)
    """The name of the task."""
    short_name: str | None = field(default=None, init=False)
    """The shortest uniquely identifiable name for task for display."""
    depends_on: PyTree[Node] = field(factory=dict)
    """A list of dependencies of task."""
    produces: PyTree[Node] = field(factory=dict)
    """A list of products of task."""
    markers: list[Mark] = field(factory=list)
    """A list of markers attached to the task function."""
    _report_sections: list[tuple[str, str, str]] = field(factory=list)
    """Reports with entries for when, what, and content."""
    attributes: dict[Any, Any] = field(factory=dict)
    """A dictionary to store additional information of the task."""

    def __attrs_post_init__(self: Task) -> None:
        """Change class after initialization."""
        if self.name is None:
            self.name = self.path.as_posix() + "::" + self.base_name

        if self.short_name is None:
            self.short_name = self.name

    def state(self, hash: bool = False) -> str | None:  # noqa: A002
        if hash and self.path.exists():
            return hashlib.sha256(self.path.read_bytes()).hexdigest()
        if not hash and self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def execute(self, **kwargs: Any) -> None:
        """Execute the task."""
        self.function(**kwargs)

    def add_report_section(self, when: str, key: str, content: str) -> None:
        """Add sections which will be displayed in report like stdout or stderr."""
        if content:
            self._report_sections.append((when, key, content))


@define(kw_only=True)
class PathNode(Node):
    """The class for a node which is a path."""

    name: str = ""
    """Name of the node which makes it identifiable in the DAG."""
    value: Path | None = None
    """Value passed to the decorator which can be requested inside the function."""
    path: Path | None = None
    """Path to the file."""

    @classmethod
    @functools.lru_cache
    def from_path(cls, path: Path) -> PathNode:
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            raise ValueError("Node must be instantiated from absolute path.")
        return cls(name=path.as_posix(), value=path, path=path)

    def state(self) -> str | None:
        """Calculate the state of the node.

        The state is given by the modification timestamp.

        """
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None


@define(kw_only=True)
class PythonNode(Node):
    """The class for a node which is a Python object."""

    name: str = ""
    """Name of the node."""
    value: Any | None = None
    """Value of the node."""
    hash: bool = False  # noqa: A003
    """Whether the value should be hashed to determine the state."""

    def state(self) -> str | None:
        """Calculate state of the node.

        If ``hash = False``, the function returns ``"0"``, a constant hash value, so the
        :class:`PythonNode` is ignored when checking for a changed state of the task.

        If ``hash = True``, :func:`hash` is used for all types except strings.

        The hash for strings is calculated using hashlib because ``hash("asd")`` returns
        a different value every invocation since the hash of strings is salted with a
        random integer and it would confuse users.

        """
        if self.hash:
            if isinstance(self.value, str):
                return str(hashlib.sha256(self.value.encode()).hexdigest())
            return str(hash(self.value))
        return "0"
