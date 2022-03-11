"""Deals with nodes which are dependencies or products of a task."""
from __future__ import annotations

import functools
from abc import ABCMeta
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

import attr
from _pytask.exceptions import NodeNotFoundError


if TYPE_CHECKING:
    from _pytask.mark import Mark


class MetaNode(metaclass=ABCMeta):
    """Meta class for nodes."""

    name: str
    path: Path

    @abstractmethod
    def state(self) -> str | None:
        ...


@attr.s(kw_only=True)
class Task:
    """The class for tasks which are Python functions."""

    base_name = attr.ib(type=str)
    """str: The base name of the task."""
    path = attr.ib(type=Path)
    """pathlib.Path: Path to the file where the task was defined."""
    function = attr.ib(type=Callable[..., Any])
    """Callable[..., Any]: The task function."""
    short_name = attr.ib(default=None, type=Optional[str], init=False)
    """str: The shortest uniquely identifiable name for task for display."""
    depends_on = attr.ib(factory=dict, type=Dict[str, MetaNode])
    """Dict[str, MetaNode]: A list of dependencies of task."""
    produces = attr.ib(factory=dict, type=Dict[str, MetaNode])
    """Dict[str, MetaNode]: A list of products of task."""
    markers = attr.ib(factory=list, type=List["Mark"])
    """Optional[List[Mark]]: A list of markers attached to the task function."""
    kwargs = attr.ib(factory=dict, type=Dict[str, Any])
    """Dict[str, Any]: A dictionary with keyword arguments supplied to the task."""
    _report_sections = attr.ib(factory=list, type=List[Tuple[str, str, str]])
    """List[Tuple[str, str, str]]: Reports with entries for when, what, and content."""
    attributes = attr.ib(factory=dict, type=Dict[Any, Any])
    """Dict[Any, Any]: A dictionary to store additional information of the task."""

    def __attrs_post_init__(self: Task) -> None:
        """Change class after initialization."""
        if self.short_name is None:
            self.short_name = self.name

    @property
    def name(self) -> str:
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


@attr.s
class FilePathNode(MetaNode):
    """The class for a node which is a path."""

    name = attr.ib(type=str)
    """str: Name of the node which makes it identifiable in the DAG."""
    value = attr.ib(type=Path)
    """Any: Value passed to the decorator which can be requested inside the function."""
    path = attr.ib(type=Path)
    """pathlib.Path: Path to the FilePathNode."""

    @classmethod
    @functools.lru_cache()
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
        else:
            return str(self.path.stat().st_mtime)
