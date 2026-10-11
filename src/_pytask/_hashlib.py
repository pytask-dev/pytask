from __future__ import annotations

import hashlib
import os
import sys
from hashlib import file_digest
from pathlib import Path
from typing import Any

from upath import UPath

_LOCAL_UPATH_PROTOCOLS = frozenset(("", "file", "local"))
_WINDOWS_DRIVE_PREFIX_LENGTH = 3


def hash_value(value: Any) -> int | str:
    """Hash values.

    Compute the hash of paths, strings, and bytes with a hash function or otherwise the
    hashes are salted.

    The hash of None constant https://github.com/python/cpython/pull/99541 starting with
    Python 3.12.

    """
    if value is None:
        return 0xFCA86420
    if isinstance(value, (tuple, list)):
        value = "".join(str(hash_value(i)) for i in value)
    if isinstance(value, UPath):
        if value.protocol in _LOCAL_UPATH_PROTOCOLS:
            local_path = value.path
            if (
                sys.platform == "win32"
                and local_path.startswith("/")
                and len(local_path) >= _WINDOWS_DRIVE_PREFIX_LENGTH
                and local_path[1].isalpha()
                and local_path[2] == ":"
            ):
                local_path = local_path[1:]
            value = os.fspath(Path(local_path))
        else:
            value = str(value)
    elif isinstance(value, os.PathLike):
        value = os.fspath(value)
    if isinstance(value, str):
        value = value.encode()
    if isinstance(value, bytes):
        return hashlib.sha256(value).hexdigest()
    return hash(value)
