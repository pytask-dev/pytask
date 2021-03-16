import os
import sys

from rich.console import Console


if sys.platform == "win32" and "WT_SESSION" not in os.environ:
    _COLOR_SYSTEM = None
else:
    _COLOR_SYSTEM = "auto"


console = Console(color_system=_COLOR_SYSTEM)
