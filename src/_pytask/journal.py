"""Helpers for append-only JSONL journals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Generic
from typing import TypeVar

import msgspec

if TYPE_CHECKING:
    from pathlib import Path

T = TypeVar("T")


@dataclass(frozen=True)
class JsonlJournal(Generic[T]):
    """Append-only JSONL journal with best-effort recovery."""

    path: Path
    type_: type[T]

    def append(self, payload: msgspec.Struct) -> None:
        """Append a JSON line to the journal."""
        with self.path.open("ab") as journal_file:
            journal_file.write(msgspec.json.encode(payload) + b"\n")

    def read(self) -> list[T]:
        """Read entries, keeping valid entries on decode errors."""
        if not self.path.exists():
            return []

        entries: list[T] = []
        data = self.path.read_bytes()
        offset = 0
        for line in data.splitlines(keepends=True):
            stripped = line.strip()
            if not stripped:
                offset += len(line)
                continue
            try:
                entries.append(msgspec.json.decode(stripped, type=self.type_))
            except msgspec.DecodeError:
                with self.path.open("rb+") as journal_file:
                    journal_file.truncate(offset)
                return entries
            offset += len(line)
        return entries

    def delete(self) -> None:
        """Delete the journal if it exists."""
        if self.path.exists():
            self.path.unlink()
