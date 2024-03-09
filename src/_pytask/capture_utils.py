"""A module for enums shared across the codebase."""

from __future__ import annotations

import enum


class ShowCapture(enum.Enum):
    NO = "no"
    STDOUT = "stdout"
    STDERR = "stderr"
    ALL = "all"


class CaptureMethod(enum.Enum):
    FD = "fd"
    NO = "no"
    SYS = "sys"
    TEE_SYS = "tee-sys"
