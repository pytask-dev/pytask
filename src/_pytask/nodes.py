"""Deals with nodes which are dependencies or products of a task."""
from __future__ import annotations

import functools
from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

from attrs import define
from attrs import field


if TYPE_CHECKING:
    from _pytask.mark import Mark


__all__ = ["FilePathNode", "MetaNode", "Product", "Task"]


@define(frozen=True)
class ProductType:
    """A class to mark products."""


Product = ProductType()


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes."""

    name: str
    """str: The name of node that must be unique."""

    @abstractmethod
    def state(self) -> Any:
        ...


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
    depends_on: dict[str, MetaNode] = field(factory=dict)
    """A list of dependencies of task."""
    produces: dict[str, MetaNode] = field(factory=dict)
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

    def state(self) -> str | None:
        if self.path.exists():
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
class FilePathNode(MetaNode):
    """The class for a node which is a path."""

    name: str
    """str: Name of the node which makes it identifiable in the DAG."""
    value: Path
    """Any: Value passed to the decorator which can be requested inside the function."""
    path: Path
    """pathlib.Path: Path to the FilePathNode."""

    def state(self) -> str | None:
        if self.path.exists():
            return str(self.path.stat().st_mtime)
        return None

    @classmethod
    @functools.lru_cache
    def from_path(cls, path: Path) -> FilePathNode:
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            raise ValueError("FilePathNode must be instantiated from absolute path.")
        return cls(name=path.as_posix(), value=path, path=path)


@define(kw_only=True)
class PythonNode(MetaNode):
    """The class for a node which is a Python object."""

    value: Any
    hash: bool = False  # noqa: A003
    name: str = ""

    def __attrs_post_init__(self) -> None:
        if not self.name:
            self.name = str(self.value)

    def state(self) -> str | None:
        if self.hash:
            return str(hash(self.value))
        return str(0)
