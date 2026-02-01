"""Runtime storage with an append-only journal."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

import msgspec

from _pytask.journal import JsonlJournal

if TYPE_CHECKING:
    from pathlib import Path

    from _pytask.node_protocols import PTask


class _RuntimeEntry(msgspec.Struct):
    id: str
    date: float
    duration: float


class _RuntimeFile(msgspec.Struct, forbid_unknown_fields=False):
    task: list[_RuntimeEntry] = msgspec.field(default_factory=list)


class _RuntimeJournalEntry(msgspec.Struct, forbid_unknown_fields=False):
    id: str
    date: float
    duration: float


def _runtimes_path(root: Path) -> Path:
    return root / ".pytask" / "runtimes.json"


def _journal_path(path: Path) -> Path:
    return path.with_suffix(".journal")


def _journal(path: Path) -> JsonlJournal[_RuntimeJournalEntry]:
    return JsonlJournal(path=_journal_path(path), type_=_RuntimeJournalEntry)


def _read_runtimes(path: Path) -> _RuntimeFile | None:
    if not path.exists():
        return None
    try:
        data = msgspec.json.decode(path.read_bytes(), type=_RuntimeFile)
    except msgspec.DecodeError:
        path.unlink()
        return None
    return data


def _write_runtimes(path: Path, runtimes: _RuntimeFile) -> None:
    data = msgspec.json.encode(runtimes)
    tmp = path.with_suffix(f"{path.suffix}.tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _read_journal(
    journal: JsonlJournal[_RuntimeJournalEntry],
) -> list[_RuntimeJournalEntry]:
    return journal.read()


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
        task=list(index.values()),
    )


@dataclass
class RuntimeState:
    path: Path
    runtimes: _RuntimeFile
    journal: JsonlJournal[_RuntimeJournalEntry]
    _index: dict[str, _RuntimeEntry] = field(init=False, default_factory=dict)
    _dirty: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self._rebuild_index()

    @classmethod
    def from_root(cls, root: Path) -> RuntimeState:
        path = _runtimes_path(root)
        journal = _journal(path)
        existing = _read_runtimes(path)
        journal_entries = _read_journal(journal)
        if existing is None:
            runtimes = _RuntimeFile(
                task=[],
            )
            runtimes = _apply_journal(runtimes, journal_entries)
            state = cls(path=path, runtimes=runtimes, journal=journal)
        else:
            runtimes = _apply_journal(existing, journal_entries)
            state = cls(path=path, runtimes=runtimes, journal=journal)

        if journal_entries:
            state._dirty = True
        return state

    def _rebuild_index(self) -> None:
        self._index = {entry.id: entry for entry in self.runtimes.task}

    def update_task(self, task: PTask, start: float, end: float) -> None:
        task_id = task.name
        entry = _RuntimeEntry(id=task_id, date=start, duration=end - start)
        self._index[entry.id] = entry
        self.runtimes = _RuntimeFile(
            task=list(self._index.values()),
        )
        self._rebuild_index()
        journal_entry = _RuntimeJournalEntry(
            id=entry.id,
            date=entry.date,
            duration=entry.duration,
        )
        self.journal.append(journal_entry)
        self._dirty = True

    def get_duration(self, task: PTask) -> float | None:
        task_id = task.name
        entry = self._index.get(task_id)
        if entry is None:
            return None
        return entry.duration

    def flush(self) -> None:
        if not self._dirty:
            return
        _write_runtimes(self.path, self.runtimes)
        self.journal.delete()
        self._dirty = False
