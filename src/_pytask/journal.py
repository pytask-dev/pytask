"""Helpers for append-only JSONL journals."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import TypeVar

import msgspec

if TYPE_CHECKING:
    from pathlib import Path

T = TypeVar("T")


def append_jsonl(path: Path, payload: msgspec.Struct) -> None:
    """Append a JSON line to the journal."""
    with path.open("ab") as journal_file:
        journal_file.write(msgspec.json.encode(payload) + b"\n")


def read_jsonl(path: Path, *, type_: type[T]) -> list[T]:
    """Read JSONL entries from a journal, stopping at the first invalid line."""
    if not path.exists():
        return []

    entries: list[T] = []
    for line in path.read_bytes().splitlines():
        if not line.strip():
            continue
        try:
            entries.append(msgspec.json.decode(line, type=type_))
        except msgspec.DecodeError:
            break
    return entries


def delete_if_exists(path: Path) -> None:
    """Delete a file if it exists."""
    if path.exists():
        path.unlink()
