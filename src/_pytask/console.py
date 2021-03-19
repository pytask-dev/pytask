import os
import sys

from rich.console import Console


_IS_WSL = "IS_WSL" in os.environ or "WSL_DISTRO_NAME" in os.environ
_IS_WINDOWS_TERMINAL = "WT_SESSION" in os.environ
_IS_WINDOWS = sys.platform == "win32"


if (_IS_WINDOWS and not _IS_WINDOWS_TERMINAL) or _IS_WSL:
    _IS_LEGACY_WINDOWS = True
else:
    _IS_LEGACY_WINDOWS = False


_COLOR_SYSTEM = None if _IS_LEGACY_WINDOWS else "auto"


ARROW_DOWN_ICON = "|" if _IS_LEGACY_WINDOWS else "⬇"
FILE_ICON = "" if _IS_LEGACY_WINDOWS else "📄 "
PYTHON_ICON = "" if _IS_LEGACY_WINDOWS else "🐍 "
TASK_ICON = "" if _IS_LEGACY_WINDOWS else "📝 "


console = Console(color_system=_COLOR_SYSTEM)
