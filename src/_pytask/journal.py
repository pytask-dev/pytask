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
        """Read entries, stopping at the first invalid line."""
        if not self.path.exists():
            return []

        entries: list[T] = []
        for line in self.path.read_bytes().splitlines():
            if not line.strip():
                continue
            try:
                entries.append(msgspec.json.decode(line, type=self.type_))
            except msgspec.DecodeError:
                break
        return entries

    def delete(self) -> None:
        """Delete the journal if it exists."""
        if self.path.exists():
            self.path.unlink()
