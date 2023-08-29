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
from _pytask.node_protocols import PPathNode
from _pytask.tree_util import PyTree
from _pytask.tree_util import tree_leaves
from _pytask.tree_util import tree_structure
from attrs import define
from attrs import field


if TYPE_CHECKING:
    from _pytask.mark import Mark


__all__ = ["PathNode", "Product", "Task"]


@define(frozen=True)
class ProductType:
    """A class to mark products."""


Product = ProductType()
"""ProductType: A singleton to mark products in annotations."""


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
        """Return the state of the node."""
        if hash and self.path.exists():
            return hashlib.sha256(self.path.read_bytes()).hexdigest()
        if not hash and self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    def execute(self, **kwargs: Any) -> None:
        """Execute the task."""
        out = self.function(**kwargs)

        if "return" in self.produces:
            structure_out = tree_structure(out)
            structure_return = tree_structure(self.produces["return"])
            # strict must be false when none is leaf.
            if not structure_return.is_prefix(structure_out, strict=False):
                raise ValueError(
                    "The structure of the return annotation is not a subtree of the "
                    "structure of the function return.\n\nFunction return: "
                    f"{structure_out}\n\nReturn annotation: {structure_return}"
                )

            nodes = tree_leaves(self.produces["return"])
            values = structure_return.flatten_up_to(out)
            for node, value in zip(nodes, values):
                node.save(value)

    def add_report_section(self, when: str, key: str, content: str) -> None:
        """Add sections which will be displayed in report like stdout or stderr."""
        if content:
            self._report_sections.append((when, key, content))


@define(kw_only=True)
class PathNode(PPathNode):
    """The class for a node which is a path."""

    name: str = ""
    """Name of the node which makes it identifiable in the DAG."""
    path: Path | None = None
    """The path to the file."""

    def from_annot(self, value: Path) -> None:
        """Set path and if other attributes are not set, set sensible defaults."""
        if not isinstance(value, Path):
            raise TypeError("'value' must be a 'pathlib.Path'.")
        if not self.name:
            self.name = value.as_posix()
        self.path = value

    @classmethod
    @functools.lru_cache
    def from_path(cls, path: Path) -> PathNode:
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            raise ValueError("Node must be instantiated from absolute path.")
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
            raise TypeError(
                f"'PathNode' can only save 'str' and 'bytes', not {type(value)}"
            )


@define(kw_only=True)
class PythonNode(Node):
    """The class for a node which is a Python object."""

    name: str = ""
    """Name of the node."""
    value: Any = None
    """Value of the node."""
    hash: bool = False  # noqa: A003
    """Whether the value should be hashed to determine the state."""

    def load(self) -> Any:
        """Load the value."""
        return self.value

    def save(self, value: Any) -> None:
        """Save the value."""
        self.value = value

    def from_annot(self, value: Any) -> None:
        """Set the value from a function annotation."""
        self.value = value

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
