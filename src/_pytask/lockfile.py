"""Support for the pytask lock file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import msgspec
from packaging.version import Version
from upath import UPath

from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.nodes import PythonNode
from _pytask.pluginmanager import hookimpl

if TYPE_CHECKING:
    from _pytask.session import Session

CURRENT_LOCKFILE_VERSION = "1.0"


class LockfileError(Exception):
    """Raised when reading or writing a lockfile fails."""


class LockfileVersionError(LockfileError):
    """Raised when a lockfile version is not supported."""


class _State(msgspec.Struct):
    value: str


class _NodeEntry(msgspec.Struct):
    id: str
    state: _State


class _TaskEntry(msgspec.Struct):
    id: str
    state: _State
    depends_on: list[_NodeEntry] = msgspec.field(default_factory=list)
    produces: list[_NodeEntry] = msgspec.field(default_factory=list)


class _Lockfile(msgspec.Struct, forbid_unknown_fields=False):
    lock_version: str = msgspec.field(name="lock-version")
    task: list[_TaskEntry] = msgspec.field(default_factory=list)


def _relative_path(path: Path, root: Path) -> str:
    if isinstance(path, UPath) and path.protocol:
        return str(path)
    try:
        rel = os.path.relpath(path, root)
    except ValueError:
        return path.as_posix()
    return Path(rel).as_posix()


def build_portable_task_id(task: PTask, root: Path) -> str:
    if isinstance(task, PTaskWithPath):
        base_name = getattr(task, "base_name", None) or task.name
        return f"{_relative_path(task.path, root)}::{base_name}"
    return task.name


def _build_portable_task_id_from_parts(
    task_path: Path | None, task_name: str, root: Path
) -> str:
    if task_path is None:
        return task_name
    return f"{_relative_path(task_path, root)}::{task_name}"


def build_portable_node_id(node: PNode, root: Path) -> str:
    if isinstance(node, PythonNode) and node.node_info:
        task_id = _build_portable_task_id_from_parts(
            node.node_info.task_path, node.node_info.task_name, root
        )
        node_id = f"{task_id}::{node.node_info.arg_name}"
        if node.node_info.path:
            suffix = "-".join(str(p) for p in node.node_info.path)
            node_id = f"{node_id}::{suffix}"
        return node_id
    if isinstance(node, PPathNode):
        return _relative_path(node.path, root)
    return node.name


def read_lockfile(path: Path) -> _Lockfile | None:
    if not path.exists():
        return None

    raw = msgspec.toml.decode(path.read_bytes())
    if not isinstance(raw, dict):
        msg = "Lockfile has invalid format."
        raise LockfileError(msg)

    version = raw.get("lock-version")
    if not isinstance(version, str):
        msg = "Lockfile is missing 'lock-version'."
        raise LockfileError(msg)

    if Version(version) > Version(CURRENT_LOCKFILE_VERSION):
        msg = (
            f"Unsupported lock-version {version!r}. "
            f"Current version is {CURRENT_LOCKFILE_VERSION}."
        )
        raise LockfileVersionError(msg)

    lockfile = msgspec.toml.decode(path.read_bytes(), type=_Lockfile)

    if Version(version) < Version(CURRENT_LOCKFILE_VERSION):
        lockfile = _Lockfile(
            lock_version=CURRENT_LOCKFILE_VERSION,
            task=lockfile.task,
        )
    return lockfile


def _normalize_lockfile(lockfile: _Lockfile) -> _Lockfile:
    tasks = []
    for task in sorted(lockfile.task, key=lambda entry: entry.id):
        depends_on = sorted(task.depends_on, key=lambda entry: entry.id)
        produces = sorted(task.produces, key=lambda entry: entry.id)
        tasks.append(
            _TaskEntry(
                id=task.id,
                state=task.state,
                depends_on=depends_on,
                produces=produces,
            )
        )
    return _Lockfile(lock_version=CURRENT_LOCKFILE_VERSION, task=tasks)


def write_lockfile(path: Path, lockfile: _Lockfile) -> None:
    normalized = _normalize_lockfile(lockfile)
    data = msgspec.toml.encode(normalized)
    tmp = path.with_suffix(f"{path.suffix}.tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _build_task_entry(session: Session, task: PTask, root: Path) -> _TaskEntry | None:
    task_state = task.state()
    if task_state is None:
        return None

    dag = session.dag
    predecessors = set(dag.predecessors(task.signature))
    successors = set(dag.successors(task.signature))

    depends_on = []
    for node_signature in predecessors:
        node = (
            dag.nodes[node_signature].get("task") or dag.nodes[node_signature]["node"]
        )
        if not isinstance(node, (PNode, PTask)):
            continue
        state = node.state()
        if state is None:
            continue
        node_id = (
            build_portable_task_id(node, root)
            if isinstance(node, PTask)
            else build_portable_node_id(node, root)
        )
        depends_on.append(_NodeEntry(id=node_id, state=_State(state)))

    produces = []
    for node_signature in successors:
        node = (
            dag.nodes[node_signature].get("task") or dag.nodes[node_signature]["node"]
        )
        if not isinstance(node, (PNode, PTask)):
            continue
        state = node.state()
        if state is None:
            continue
        node_id = (
            build_portable_task_id(node, root)
            if isinstance(node, PTask)
            else build_portable_node_id(node, root)
        )
        produces.append(_NodeEntry(id=node_id, state=_State(state)))

    return _TaskEntry(
        id=build_portable_task_id(task, root),
        state=_State(task_state),
        depends_on=depends_on,
        produces=produces,
    )


@dataclass
class LockfileState:
    path: Path
    root: Path
    use_lockfile_for_skip: bool
    lockfile: _Lockfile
    _task_index: dict[str, _TaskEntry] = field(init=False, default_factory=dict)
    _node_index: dict[str, dict[str, str]] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self._rebuild_indexes()

    @classmethod
    def from_path(cls, path: Path, root: Path) -> LockfileState:
        existing = read_lockfile(path)
        if existing is None:
            lockfile = _Lockfile(
                lock_version=CURRENT_LOCKFILE_VERSION,
                task=[],
            )
            return cls(
                path=path,
                root=root,
                use_lockfile_for_skip=False,
                lockfile=lockfile,
            )
        return cls(
            path=path,
            root=root,
            use_lockfile_for_skip=True,
            lockfile=existing,
        )

    def _rebuild_indexes(self) -> None:
        self._task_index = {task.id: task for task in self.lockfile.task}
        self._node_index = {}
        for task in self.lockfile.task:
            nodes = {}
            for entry in task.depends_on + task.produces:
                nodes[entry.id] = entry.state.value
            self._node_index[task.id] = nodes

    def get_task_entry(self, task_id: str) -> _TaskEntry | None:
        return self._task_index.get(task_id)

    def get_node_state(self, task_id: str, node_id: str) -> str | None:
        return self._node_index.get(task_id, {}).get(node_id)

    def update_task(self, session: Session, task: PTask) -> None:
        entry = _build_task_entry(session, task, self.root)
        if entry is None:
            return
        self._task_index[entry.id] = entry
        self.lockfile = _Lockfile(
            lock_version=CURRENT_LOCKFILE_VERSION,
            task=list(self._task_index.values()),
        )
        self._rebuild_indexes()
        write_lockfile(self.path, self.lockfile)


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Initialize the lockfile state."""
    path = config["root"] / "pytask.lock"
    config["lockfile_path"] = path
    config["lockfile_state"] = LockfileState.from_path(path, config["root"])
