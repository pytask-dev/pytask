from __future__ import annotations

from typing import Tuple

import attr


@attr.s(kw_only=True)
class WarningReport:
    message = attr.ib(type=str)
    fs_location = attr.ib(type=Tuple[str, int])
    id_ = attr.ib(type=str)
