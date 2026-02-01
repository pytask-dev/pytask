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

from _pytask.journal import JsonlJournal
from _pytask.node_protocols import PNode
from _pytask.node_protocols import PPathNode
from _pytask.node_protocols import PTask
from _pytask.node_protocols import PTaskWithPath
from _pytask.nodes import PythonNode
from _pytask.outcomes import ExitCode
from _pytask.pluginmanager import hookimpl

if TYPE_CHECKING:
    from _pytask.session import Session

CURRENT_LOCKFILE_VERSION = "1"


class LockfileError(Exception):
    """Raised when reading or writing a lockfile fails."""


class LockfileVersionError(LockfileError):
    """Raised when a lockfile version is not supported."""


class _TaskEntry(msgspec.Struct):
    id: str
    state: str
    depends_on: dict[str, str] = msgspec.field(default_factory=dict)
    produces: dict[str, str] = msgspec.field(default_factory=dict)


class _Lockfile(msgspec.Struct, forbid_unknown_fields=False):
    lock_version: str = msgspec.field(name="lock-version")
    task: list[_TaskEntry] = msgspec.field(default_factory=list)


class _JournalEntry(msgspec.Struct):
    lock_version: str = msgspec.field(name="lock-version")
    id: str
    state: str
    depends_on: dict[str, str] = msgspec.field(default_factory=dict)
    produces: dict[str, str] = msgspec.field(default_factory=dict)


def _encode_node_path(path: tuple[str | int, ...]) -> str:
    return msgspec.json.encode(path).decode()


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
            suffix = _encode_node_path(node.node_info.path)
            node_id = f"{node_id}::{suffix}"
        return node_id
    if isinstance(node, PPathNode):
        return _relative_path(node.path, root)
    return node.name


def _journal(path: Path) -> JsonlJournal[_JournalEntry]:
    return JsonlJournal(
        path=path.with_suffix(f"{path.suffix}.journal"), type_=_JournalEntry
    )


def _read_journal_entries(journal: JsonlJournal[_JournalEntry]) -> list[_JournalEntry]:
    entries = journal.read()
    for entry in entries:
        if Version(entry.lock_version) != Version(CURRENT_LOCKFILE_VERSION):
            msg = (
                f"Unsupported lock-version {entry.lock_version!r}. "
                f"Current version is {CURRENT_LOCKFILE_VERSION}."
            )
            raise LockfileVersionError(msg)
    return entries


def read_lockfile(path: Path) -> _Lockfile | None:
    if not path.exists():
        return None

    try:
        raw = msgspec.toml.decode(path.read_bytes())
    except msgspec.DecodeError:
        msg = "Lockfile has invalid format."
        raise LockfileError(msg) from None
    if not isinstance(raw, dict):
        msg = "Lockfile has invalid format."
        raise LockfileError(msg)

    version = raw.get("lock-version")
    if not isinstance(version, str):
        msg = "Lockfile is missing 'lock-version'."
        raise LockfileError(msg)

    if Version(version) != Version(CURRENT_LOCKFILE_VERSION):
        msg = (
            f"Unsupported lock-version {version!r}. "
            f"Current version is {CURRENT_LOCKFILE_VERSION}."
        )
        raise LockfileVersionError(msg)

    try:
        return msgspec.toml.decode(path.read_bytes(), type=_Lockfile)
    except msgspec.DecodeError:
        msg = "Lockfile has invalid format."
        raise LockfileError(msg) from None


def _normalize_lockfile(lockfile: _Lockfile) -> _Lockfile:
    tasks = []
    for task in sorted(lockfile.task, key=lambda entry: entry.id):
        depends_on = {key: task.depends_on[key] for key in sorted(task.depends_on)}
        produces = {key: task.produces[key] for key in sorted(task.produces)}
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


def _apply_journal(lockfile: _Lockfile, entries: list[_JournalEntry]) -> _Lockfile:
    if not entries:
        return lockfile
    task_index = {task.id: task for task in lockfile.task}
    for entry in entries:
        task_index[entry.id] = _TaskEntry(
            id=entry.id,
            state=entry.state,
            depends_on=entry.depends_on,
            produces=entry.produces,
        )
    return _Lockfile(
        lock_version=CURRENT_LOCKFILE_VERSION,
        task=list(task_index.values()),
    )


def _build_task_entry(session: Session, task: PTask, root: Path) -> _TaskEntry | None:
    task_state = task.state()
    if task_state is None:
        return None

    dag = session.dag
    predecessors = set(dag.predecessors(task.signature))
    successors = set(dag.successors(task.signature))

    depends_on: dict[str, str] = {}
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
        depends_on[node_id] = state

    produces: dict[str, str] = {}
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
        produces[node_id] = state

    return _TaskEntry(
        id=build_portable_task_id(task, root),
        state=task_state,
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
    _dirty: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self._rebuild_indexes()

    @classmethod
    def from_path(cls, path: Path, root: Path) -> LockfileState:
        existing = read_lockfile(path)
        journal = _journal(path)
        journal_entries = _read_journal_entries(journal)
        if existing is None:
            lockfile = _Lockfile(
                lock_version=CURRENT_LOCKFILE_VERSION,
                task=[],
            )
            lockfile = _apply_journal(lockfile, journal_entries)
            state = cls(
                path=path,
                root=root,
                use_lockfile_for_skip=bool(journal_entries),
                lockfile=lockfile,
            )
            if journal_entries:
                state._dirty = True
            return state
        lockfile = _apply_journal(existing, journal_entries)
        state = cls(
            path=path,
            root=root,
            use_lockfile_for_skip=True,
            lockfile=lockfile,
        )
        if journal_entries:
            state._dirty = True
        return state

    def _rebuild_indexes(self) -> None:
        self._task_index = {task.id: task for task in self.lockfile.task}
        self._node_index = {}
        for task in self.lockfile.task:
            nodes = {**task.depends_on, **task.produces}
            self._node_index[task.id] = nodes

    def get_task_entry(self, task_id: str) -> _TaskEntry | None:
        return self._task_index.get(task_id)

    def get_node_state(self, task_id: str, node_id: str) -> str | None:
        return self._node_index.get(task_id, {}).get(node_id)

    def update_task(self, session: Session, task: PTask) -> None:
        entry = _build_task_entry(session, task, self.root)
        if entry is None:
            return
        existing = self._task_index.get(entry.id)
        if existing == entry:
            return
        self._task_index[entry.id] = entry
        self.lockfile = _Lockfile(
            lock_version=CURRENT_LOCKFILE_VERSION,
            task=list(self._task_index.values()),
        )
        self._rebuild_indexes()
        journal = _journal(self.path)
        journal.append(
            _JournalEntry(
                lock_version=CURRENT_LOCKFILE_VERSION,
                id=entry.id,
                state=entry.state,
                depends_on=entry.depends_on,
                produces=entry.produces,
            )
        )
        self._dirty = True

    def rebuild_from_session(self, session: Session) -> None:
        if session.dag is None:
            return
        tasks = []
        for task in session.tasks:
            entry = _build_task_entry(session, task, self.root)
            if entry is not None:
                tasks.append(entry)
        self.lockfile = _Lockfile(
            lock_version=CURRENT_LOCKFILE_VERSION,
            task=tasks,
        )
        self._rebuild_indexes()
        write_lockfile(self.path, self.lockfile)
        _journal(self.path).delete()
        self._dirty = False

    def flush(self) -> None:
        if not self._dirty:
            return
        write_lockfile(self.path, self.lockfile)
        _journal(self.path).delete()
        self._dirty = False


@hookimpl
def pytask_post_parse(config: dict[str, Any]) -> None:
    """Initialize the lockfile state."""
    path = config["root"] / "pytask.lock"
    config["lockfile_path"] = path
    config["lockfile_state"] = LockfileState.from_path(path, config["root"])


@hookimpl
def pytask_unconfigure(session: Session) -> None:
    """Optionally rewrite the lockfile to drop stale entries."""
    if session.config.get("command") != "build":
        return
    if session.config.get("dry_run"):
        return
    if session.config.get("explain"):
        return
    if session.exit_code != ExitCode.OK:
        lockfile_state = session.config.get("lockfile_state")
        if lockfile_state is None:
            return
        lockfile_state.flush()
        return
    lockfile_state = session.config.get("lockfile_state")
    if lockfile_state is None:
        return
    if session.config.get("clean_lockfile"):
        lockfile_state.rebuild_from_session(session)
    else:
        lockfile_state.flush()
