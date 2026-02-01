"""Runtime storage with an append-only journal."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

import msgspec
from packaging.version import Version

from _pytask.journal import append_jsonl
from _pytask.journal import delete_if_exists
from _pytask.journal import read_jsonl

if TYPE_CHECKING:
    from pathlib import Path

    from _pytask.node_protocols import PTask

CURRENT_RUNTIME_VERSION = "1"


class RuntimeStoreError(Exception):
    """Raised when reading or writing runtime files fails."""


class RuntimeStoreVersionError(RuntimeStoreError):
    """Raised when a runtime file version is not supported."""


class _RuntimeEntry(msgspec.Struct):
    id: str
    date: float
    duration: float


class _RuntimeFile(msgspec.Struct, forbid_unknown_fields=False):
    runtime_version: str = msgspec.field(name="runtime-version")
    task: list[_RuntimeEntry] = msgspec.field(default_factory=list)


class _RuntimeJournalEntry(msgspec.Struct):
    runtime_version: str = msgspec.field(name="runtime-version")
    id: str
    date: float
    duration: float


def _runtimes_path(root: Path) -> Path:
    return root / ".pytask" / "runtimes.json"


def _journal_path(path: Path) -> Path:
    return path.with_suffix(".journal")


def _read_runtimes(path: Path) -> _RuntimeFile | None:
    if not path.exists():
        return None
    try:
        data = msgspec.json.decode(path.read_bytes(), type=_RuntimeFile)
    except msgspec.DecodeError:
        msg = "Runtime file has invalid format."
        raise RuntimeStoreError(msg) from None

    if Version(data.runtime_version) != Version(CURRENT_RUNTIME_VERSION):
        msg = (
            f"Unsupported runtime-version {data.runtime_version!r}. "
            f"Current version is {CURRENT_RUNTIME_VERSION}."
        )
        raise RuntimeStoreVersionError(msg)
    return data


def _write_runtimes(path: Path, runtimes: _RuntimeFile) -> None:
    data = msgspec.json.encode(runtimes)
    tmp = path.with_suffix(f"{path.suffix}.tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _read_journal(path: Path) -> list[_RuntimeJournalEntry]:
    journal_path = _journal_path(path)
    entries = read_jsonl(journal_path, type_=_RuntimeJournalEntry)
    for entry in entries:
        if Version(entry.runtime_version) != Version(CURRENT_RUNTIME_VERSION):
            msg = (
                f"Unsupported runtime-version {entry.runtime_version!r}. "
                f"Current version is {CURRENT_RUNTIME_VERSION}."
            )
            raise RuntimeStoreVersionError(msg)
    return entries


def _apply_journal(
    runtimes: _RuntimeFile, entries: list[_RuntimeJournalEntry]
) -> _RuntimeFile:
    if not entries:
        return runtimes
    index = {entry.id: entry for entry in runtimes.task}
    for entry in entries:
        index[entry.id] = _RuntimeEntry(
            id=entry.id, date=entry.date, duration=entry.duration
        )
    return _RuntimeFile(
        runtime_version=CURRENT_RUNTIME_VERSION,
        task=list(index.values()),
    )


def _build_task_id(task: PTask) -> str:
    return task.name


@dataclass
class RuntimeState:
    path: Path
    runtimes: _RuntimeFile
    _index: dict[str, _RuntimeEntry] = field(init=False, default_factory=dict)
    _dirty: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self._rebuild_index()

    @classmethod
    def from_root(cls, root: Path) -> RuntimeState:
        path = _runtimes_path(root)
        existing = _read_runtimes(path)
        journal_entries = _read_journal(path)
        if existing is None:
            runtimes = _RuntimeFile(
                runtime_version=CURRENT_RUNTIME_VERSION,
                task=[],
            )
            runtimes = _apply_journal(runtimes, journal_entries)
            state = cls(path=path, runtimes=runtimes)
        else:
            runtimes = _apply_journal(existing, journal_entries)
            state = cls(path=path, runtimes=runtimes)

        if journal_entries:
            state._dirty = True
        return state

    def _rebuild_index(self) -> None:
        self._index = {entry.id: entry for entry in self.runtimes.task}

    def update_task(self, task: PTask, start: float, end: float) -> None:
        task_id = _build_task_id(task)
        entry = _RuntimeEntry(id=task_id, date=start, duration=end - start)
        self._index[entry.id] = entry
        self.runtimes = _RuntimeFile(
            runtime_version=CURRENT_RUNTIME_VERSION,
            task=list(self._index.values()),
        )
        self._rebuild_index()
        journal_entry = _RuntimeJournalEntry(
            runtime_version=CURRENT_RUNTIME_VERSION,
            id=entry.id,
            date=entry.date,
            duration=entry.duration,
        )
        append_jsonl(_journal_path(self.path), journal_entry)
        self._dirty = True

    def get_duration(self, task: PTask) -> float | None:
        task_id = _build_task_id(task)
        entry = self._index.get(task_id)
        if entry is None:
            return None
        return entry.duration

    def flush(self) -> None:
        if not self._dirty:
            return
        _write_runtimes(self.path, self.runtimes)
        delete_if_exists(_journal_path(self.path))
        self._dirty = False
