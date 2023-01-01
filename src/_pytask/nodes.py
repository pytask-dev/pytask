"""Deals with nodes which are dependencies or products of a task."""
from __future__ import annotations

import functools
from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

from _pytask.exceptions import NodeNotFoundError
from attrs import define
from attrs import field


if TYPE_CHECKING:
    from _pytask.mark import Mark


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes."""

    name: str
    path: Path

    @abstractmethod
    def state(self) -> str | None:
        """Check the state of the node."""
        ...


@define(kw_only=True)
class Task:
    """The class for tasks which are Python functions."""

    base_name: str
    """str: The base name of the task."""
    path: Path
    """pathlib.Path: Path to the file where the task was defined."""
    function: Callable[..., Any]
    """Callable[..., Any]: The task function."""
    short_name: str | None = field(default=None, init=False)
    """str: The shortest uniquely identifiable name for task for display."""
    depends_on: dict[str, MetaNode] = field(factory=dict)
    """Dict[str, MetaNode]: A list of dependencies of task."""
    produces: dict[str, MetaNode] = field(factory=dict)
    """Dict[str, MetaNode]: A list of products of task."""
    markers: list[Mark] = field(factory=list)
    """Optional[List[Mark]]: A list of markers attached to the task function."""
    kwargs: dict[str, Any] = field(factory=dict)
    """Dict[str, Any]: A dictionary with keyword arguments supplied to the task."""
    _report_sections: list[tuple[str, str, str]] = field(factory=list)
    """List[Tuple[str, str, str]]: Reports with entries for when, what, and content."""
    attributes: dict[Any, Any] = field(factory=dict)
    """Dict[Any, Any]: A dictionary to store additional information of the task."""

    def __attrs_post_init__(self: Task) -> None:
        """Change class after initialization."""
        if self.short_name is None:
            self.short_name = self.name

    @property
    def name(self) -> str:
        """Return the name of the task."""
        return self.path.as_posix() + "::" + self.base_name

    def execute(self, **kwargs: Any) -> None:
        """Execute the task."""
        self.function(**kwargs)

    def state(self) -> str:
        """Return the last modified date of the file where the task is defined."""
        return str(self.path.stat().st_mtime)

    def add_report_section(self, when: str, key: str, content: str) -> None:
        """Add sections which will be displayed in report like stdout or stderr."""
        if content:
            self._report_sections.append((when, key, content))


@define
class FilePathNode(MetaNode):
    """The class for a node which is a path."""

    name: str
    """str: Name of the node which makes it identifiable in the DAG."""
    value: Path
    """Any: Value passed to the decorator which can be requested inside the function."""
    path: Path
    """pathlib.Path: Path to the FilePathNode."""

    @classmethod
    @functools.lru_cache
    def from_path(cls, path: Path) -> FilePathNode:
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            raise ValueError("FilePathNode must be instantiated from absolute path.")
        return cls(path.as_posix(), path, path)

    def state(self) -> str | None:
        """Return the last modified date for file path."""
        if not self.path.exists():
            raise NodeNotFoundError
        return str(self.path.stat().st_mtime)
