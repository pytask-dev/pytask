from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def hash_value(value: Any) -> int | str:
    """Hash values.

    Compute the hash of paths, strings, and bytes with a hash function or otherwise the
    hashes are salted.

    """
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, str):
        value = value.encode()
    if isinstance(value, bytes):
        return str(hashlib.sha256(value).hexdigest())
    return hash(value)
