"""Contains implementations of tasks and nodes following the node protocols."""
from __future__ import annotations

import functools
import hashlib
import inspect
import pickle
from pathlib import Path  # noqa: TCH003
from typing import Any
from typing import Callable
from typing import TYPE_CHECKING

from _pytask._hashlib import hash_value
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.path import hash_path
from _pytask.typing import no_default
from _pytask.typing import NoDefault
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
    depends_on: dict[str, PyTree[PNode]] = field(factory=dict)
    produces: dict[str, PyTree[PNode]] = field(factory=dict)
    markers: list[Mark] = field(factory=list)
    report_sections: list[tuple[str, str, str]] = field(factory=list)
    attributes: dict[Any, Any] = field(factory=dict)

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
    display_name
        The shortest uniquely identifiable name for task for display.
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
    display_name: str = field(default="", init=False)
    depends_on: dict[str, PyTree[PNode]] = field(factory=dict)
    produces: dict[str, PyTree[PNode]] = field(factory=dict)
    markers: list[Mark] = field(factory=list)
    report_sections: list[tuple[str, str, str]] = field(factory=list)
    attributes: dict[Any, Any] = field(factory=dict)

    def __attrs_post_init__(self: Task) -> None:
        """Change class after initialization."""
        if not self.name:
            self.name = self.path.as_posix() + "::" + self.base_name

        if not self.display_name:
            self.display_name = self.name

    def state(self) -> str | None:
        """Return the state of the node."""
        if self.path.exists():
            modification_time = self.path.stat().st_mtime
            return hash_path(self.path, modification_time)
        return None

    def execute(self, **kwargs: Any) -> None:
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

    name: str
    path: Path

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
            modification_time = self.path.stat().st_mtime
            return hash_path(self.path, modification_time)
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
        objects.

    Examples
    --------
    To allow a :class:`~pytask.PythonNode` to hash a dictionary, you need to pass your
    own hashing function. For example, from the :mod:`deepdiff` library.

    >>> from deepdiff import DeepHash
    >>> node = PythonNode(name="node", value={"a": 1}, hash=lambda x: DeepHash(x)[x])

    .. warning:: Hashing big objects can require some time.

    """

    name: str = ""
    value: Any | NoDefault = no_default
    hash: bool | Callable[[Any], bool] = False  # noqa: A003

    def load(self) -> Any:
        """Load the value."""
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
            value = self.load()
            if callable(self.hash):
                return str(self.hash(value))
            return str(hash_value(value))
        return "0"


@define
class PickleNode:
    """A node for pickle files.

    Parameters
    ----------
    name
        Name of the node which makes it identifiable in the DAG.
    path
        The path to the file.
    load_func
        A function to convert :obj:`bytes` from a pickle file to a Python object.
    dump_func
        A function to convert a Python object to :obj:`bytes`.

    """

    name: str
    path: Path
    load_func: Callable[[bytes], Any] = pickle.loads
    dump_func: Callable[[Any], bytes] = pickle.dumps

    @classmethod
    @functools.lru_cache
    def from_path(cls, path: Path) -> PickleNode:
        """Instantiate class from path to file.

        The `lru_cache` decorator ensures that the same object is not collected twice.

        """
        if not path.is_absolute():
            msg = "Node must be instantiated from absolute path."
            raise ValueError(msg)
        return cls(name=path.as_posix(), path=path)

    def state(self) -> str | None:
        if self.path.exists():
            modification_time = self.path.stat().st_mtime
            return hash_path(self.path, modification_time)
        return None

    def load(self) -> Any:
        return self.load_func(self.path.read_bytes())

    def save(self, value: Any) -> None:
        self.path.write_bytes(self.dump_func(value))
